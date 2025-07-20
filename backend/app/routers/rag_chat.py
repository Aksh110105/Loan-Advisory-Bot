from datetime import datetime
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import os

from app.services.OpenAIClient import OpenAIClient
from app.services.Serper import SerperClient
from app.database import get_db
from app.models.intent import Intent
from app.rag.load_knowledge import load_qa_from_csv
from app.rag.embeddings import embed_text

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

router = APIRouter()
openai_client = OpenAIClient()
serper_client = SerperClient()

CSV_PATH = os.path.join("Data", "loan_faq_dataset.csv")
vector_store = load_qa_from_csv(CSV_PATH)
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

EXIT_PHRASES = [
    "ok", "okay", "thanks", "thank you", "got it", "bye", "cool",
    "okay thanks", "i got it", "no more questions", "alright", "fine", "that's all"
]

def get_similarity_score(user_message: str) -> float:
    try:
        user_embedding = embed_model.encode([user_message])
        exit_embeddings = embed_model.encode(EXIT_PHRASES)
        similarities = cosine_similarity(user_embedding, exit_embeddings)[0]
        max_score = max(similarities)
        print("🧠 Cosine similarity score:", max_score)
        return max_score
    except Exception as e:
        print("⚠️ Similarity check error:", e)
        return 0.0

@router.post("/rag-chat")
async def rag_chat(
    query: dict,
    session_id: str = Header(..., convert_underscores=False),
    user_uuid: UUID = Header(..., convert_underscores=False),
    db: AsyncSession = Depends(get_db)
):
    user_message = query.get("message")
    model_name = query.get("model", "GPT-4")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")

    openai_client.set_model(model_name)

    # 🧠 Fetch context
    all_intents = (await db.execute(
        select(Intent).where(Intent.session_id == session_id).order_by(Intent.created_at.asc())
    )).scalars().all()

    context, description_lines = {}, []
    for intent in all_intents:
        if intent.user_message and intent.bot_response:
            description_lines.append(f"User: {intent.user_message}\nBot: {intent.bot_response}")
        if intent.parameters:
            for k, v in intent.parameters.items():
                if k not in context or not context[k]:
                    context[k] = v

    name = context.get("name") or next((i.parameters.get("name") for i in all_intents if i.parameters and i.parameters.get("name")), None)
    loan_type = context.get("loan_type") or next((i.parameters.get("loan_type") for i in all_intents if i.parameters and i.parameters.get("loan_type")), None)
    last_user_query = context.get("last_user_query") or user_message

    # Normalize income
    income_val = context.get("income")
    if income_val:
        try:
            cleaned = income_val.replace("₹", "").replace(",", "").strip()
            income_numeric = int(cleaned) if cleaned.isdigit() else None
            if income_numeric:
                context["income"] = f"₹{income_numeric:,}"
                if income_numeric > 500000:
                    context["high_income_flag"] = True
                    context["assumed_loan_size"] = "very high"
        except Exception as e:
            print("⚠️ Income normalization error:", e)

    # Context summary
    summary_context = f"You are looking for a {loan_type or 'loan'} in {context.get('location')} with a monthly income of {context.get('income')}, planning to apply in {context.get('timeline')}."
    if context.get("assumed_loan_size"):
        summary_context += f" Based on your income, it appears you may be seeking a {context['assumed_loan_size']} loan."
    if context.get("loan_amount"):
        summary_context += f" The user is considering a loan amount of {context['loan_amount']}."
    if name:
        summary_context = f"User Name: {name}\n" + summary_context

    description = "\n\n".join(description_lines).strip()
    query_with_context = f"{user_message}\n\nUser context: {summary_context}"

    # Step 1: RAG search
    top_matches = vector_store.search(query_with_context, embed_func=embed_text, threshold=0.4)
    best_match_score = top_matches[0][2] if top_matches else 0.0

    # Step 2: Exit similarity check (always run, regardless of match)
    similarity_score = get_similarity_score(user_message)
    if similarity_score >= 0.75:
        print("🧠 Message is potentially an exit phrase.")
        confirm_exit = openai_client.is_exit(user_message, summary_context)
        print("🤖 LLM confirms exit:", confirm_exit)
        if confirm_exit:
            farewell = f"👋 Glad I could help, {name or 'there'}! Let me know if you need anything else later. Goodbye!"
            await save_intent(user_uuid, session_id, user_message, farewell, context, db, name, description, loan_type, last_user_query, intent="farewell")
            return {"response": farewell}

    # Step 3: No strong FAQ match — skip Serper if no RAG
    if not top_matches or best_match_score < 0.55:
        print("📉 No strong FAQ match — no Serper fallback.")
        msg = "❌ Couldn't find relevant knowledge — try rephrasing."
        await save_intent(user_uuid, session_id, user_message, msg, context, db, name, description, loan_type, last_user_query)
        return {"response": msg}

    # Step 4: Proceed with Serper + LLM
    top_q, top_a, _ = top_matches[0]
    kb_context = f"📚 FAQ Match:\nQ: {top_q}\nA: {top_a}\n\n"

    try:
        web_query = openai_client.generate_response(f"Write a short and relevant web search query to help answer:\n'{user_message}'")
        print("🔎 Web search query:", web_query)
        web_results = serper_client.search(web_query)
        links = [item["link"] for item in web_results.get("organic", [])[:3]]
        web_summary = openai_client.generate_response(f"Summarize helpful information from these links:\n" + "\n".join(links)) if links else ""
    except Exception as e:
        print(f"⚠️ Web search error: {e}")
        web_summary = ""

    final_prompt = (
        f"User Message: {user_message}\n\n"
        f"User Context: {summary_context}\n\n"
        f"{kb_context}"
        f"🔗 Web Info:\n{web_summary}\n\n"
        f"🎯 Provide a specific, helpful, and clear answer relevant to Indian loan users."
    )

    try:
        response = openai_client.generate_response(final_prompt)
    except Exception as e:
        response = f"⚠️ OpenAI error: {str(e)}"

    await save_intent(user_uuid, session_id, user_message, response, context, db, name, description, loan_type, last_user_query)
    return {"response": response}

# Save intent
async def save_intent(
    user_uuid: UUID,
    session_id: str,
    user_message: str,
    bot_response: str,
    parameters: dict,
    db: AsyncSession,
    name: str = None,
    description: str = None,
    loan_type: str = None,
    last_user_query: str = None,
    intent: str = "loan_rag"
):
    new_intent = Intent(
        user_uuid=user_uuid,
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
        intent=intent,
        parameters=parameters,
        context={"summary": f"user needs: {parameters}"},
        created_at=datetime.utcnow(),
        name=name or parameters.get("name"),
        description=description,
        loan_type=loan_type or parameters.get("loan_type"),
        last_user_query=last_user_query or parameters.get("last_user_query")
    )
    db.add(new_intent)
    await db.commit()
    await db.refresh(new_intent)
