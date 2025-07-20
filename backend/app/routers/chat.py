from datetime import datetime
from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import os, re

from app.services.OpenAIClient import OpenAIClient
from app.services.Serper import SerperClient
from app.database import get_db
from app.models.intent import Intent
from app.rag.load_knowledge import load_qa_from_csv
from app.rag.embeddings import embed_text, cosine_similarity

router = APIRouter()
openai_client = OpenAIClient()
serper_client = SerperClient()

REQUIRED_SLOTS = ["name", "location", "income", "timeline"]
CSV_PATH = os.path.join("Data", "loan_faq_dataset.csv")
vector_store = load_qa_from_csv(CSV_PATH)
EXIT_PHRASES = ["ok", "okay", "thanks", "thank you", "got it", "bye", "cool", "okay thanks", "i got it", "no more questions"]

@router.post("/chat")
async def chat_endpoint(
    query: dict,
    session_id: str = Header(..., convert_underscores=False),
    user_uuid: UUID = Header(..., convert_underscores=False),
    db: AsyncSession = Depends(get_db)
):
    user_message = query.get("message")
    model_name = query.get("model", "GPT-4")
    if not user_message:
        raise HTTPException(status_code=400, detail="No message provided")

    openai_client.set_model(model_name)

    # Last intent
    last_intent = (await db.execute(
        select(Intent).where(Intent.session_id == session_id).order_by(Intent.created_at.desc()).limit(1)
    )).scalar_one_or_none()

    last_params = last_intent.parameters if last_intent and last_intent.parameters else {}
    already_in_loan_flow = last_intent and last_intent.intent == "loan_inquiry"

    # High-income follow-up
    if last_params.get("high_income_flag") and last_params.get("awaiting_loan_amount"):
        cleaned = user_message.replace(",", "").strip()
        if cleaned.isdigit():
            last_params["loan_amount"] = f"₹{int(cleaned):,}"
            last_params["awaiting_loan_amount"] = False
            user_message = f"I am considering a loan of ₹{int(cleaned):,}."
            already_in_loan_flow = True

    # Handle name response
    if last_intent and last_intent.bot_response.startswith("🙋‍♂️ May I know your name?"):
        name_candidate = user_message.strip()
        if name_candidate.replace(" ", "").isalpha():
            last_params["name"] = name_candidate.title()
            user_message = f"My name is {name_candidate.title()}"
            already_in_loan_flow = True

    # First message — classify intent (greeting / loan / irrelevant)
    if not already_in_loan_flow and not last_intent:
        # 1. Check if greeting
        is_greeting = openai_client.is_greeting(user_message)
        if is_greeting:
            msg = (
                "👋 Hi there! I’m your Loan Advisor Chatbot. "
                "I can assist you with personal, home, education, vehicle, business, or MSME loans. Please let me know your requirement."
            )
            await save_intent(user_uuid, session_id, user_message, msg, {}, db, intent="greeting")
            return {"response": msg, "mode": "chat"}

        # 2. Check if loan-related
        if not openai_client.is_loan_related(user_message):
            msg = "❌ I can only assist with **loan-related queries** like personal, home, education, vehicle, business, or MSME loans."
            await save_intent(user_uuid, session_id, user_message, msg, {}, db, intent="irrelevant")
            return {"response": msg, "mode": "chat"}

    # Extract parameters
    extracted = openai_client.extract_parameters(user_message)
    merged = {
        **last_params,
        **{k: v for k, v in extracted.items() if v and isinstance(v, (str, int)) and str(v).lower() != "unknown"}
    }
    merged["last_user_query"] = user_message

    # Name fallback
    if "name" not in merged:
        name_match = re.search(r"\bmy name is (\w+)", user_message, re.IGNORECASE)
        if name_match:
            merged["name"] = name_match.group(1).capitalize()

    # Infer loan_type
    if "loan_type" not in merged:
        for typ in ["personal", "home", "education", "vehicle", "business", "msme"]:
            if typ in user_message.lower():
                merged["loan_type"] = typ
                break

    # Loan relevance re-check
    if not any(k in user_message.lower() for k in ["loan", "personal", "home", "education", "vehicle", "business", "msme"]) and not merged.get("loan_type"):
        if not openai_client.is_loan_related(user_message):
            msg = "❌ I can only assist with **loan-related queries** like personal, home, education, vehicle, business, or MSME loans."
            await save_intent(user_uuid, session_id, user_message, msg, {}, db, intent="irrelevant")
            return {"response": msg, "mode": "chat"}

    # Normalize income
    if "income" in merged:
        try:
            income_val = merged["income"]
            income_numeric = None
            if isinstance(income_val, int):
                income_numeric = income_val
            elif isinstance(income_val, str):
                cleaned = income_val.replace("₹", "").replace(",", "").strip()
                if cleaned.isdigit():
                    income_numeric = int(cleaned)
            if income_numeric:
                merged["income"] = f"₹{income_numeric:,}"
                if income_numeric > 500000 and not merged.get("high_income_flag"):
                    merged["high_income_flag"] = True
                    merged["assumed_loan_size"] = "very high"
                    merged["awaiting_loan_amount"] = True
                    msg = (
                        f"🤔 With a monthly income of ₹{income_numeric:,}, are you sure you need a loan? "
                        "Please share the purpose or amount you’re considering."
                    )
                    await save_intent(user_uuid, session_id, user_message, msg, merged, db, intent="high_income_check")
                    return {"response": msg, "mode": "chat"}
        except Exception as e:
            print("⚠️ Income normalization error:", e)

    # Slot filling
    for slot in REQUIRED_SLOTS:
        if not merged.get(slot):
            followup = {
                "name": "🙋‍♂️ May I know your name?",
                "location": "📍 May I know your location (city/state)?",
                "income": "💰 Could you please share your monthly income?",
                "timeline": "🗓️ When are you planning to take the loan (e.g. this month, in 2 months)?"
            }[slot]
            await save_intent(user_uuid, session_id, user_message, followup, merged, db, intent="loan_inquiry")
            return {"response": followup, "mode": "chat"}

    # COSINE SIMILARITY + LLM EXIT CONFIRMATION
    query_emb = embed_text(user_message)
    exit_scores = [cosine_similarity(query_emb, embed_text(p)) for p in EXIT_PHRASES]
    if max(exit_scores) > 0.75:
        summary_context = f"User Query: {user_message}\n\nKnown Info: {merged}"
        decision = openai_client.generate_response(
            f"{summary_context}\n\nIs the user trying to politely end the conversation? Reply only YES or NO."
        ).strip().lower()
        if decision.startswith("yes"):
            farewell_msg = f"👋 Glad I could help, {merged.get('name') or 'there'}! Feel free to come back anytime if you have more questions. Goodbye!"
            await save_intent(user_uuid, session_id, user_message, farewell_msg, merged, db, intent="farewell")
            return {"response": farewell_msg, "mode": "chat"}

    # RAG fallback
    summary_context = f"You are looking for a {merged.get('loan_type', 'loan')} in {merged['location']} with a monthly income of {merged['income']}, planning to apply in {merged['timeline']}"
    if merged.get("assumed_loan_size"):
        summary_context += f". Based on your income, it appears you may be seeking a {merged['assumed_loan_size']} loan."
    if merged.get("loan_amount"):
        summary_context += f" The user is considering a loan amount of {merged['loan_amount']}."
    if merged.get("name"):
        summary_context = f"User Name: {merged['name']}\n" + summary_context

    query_with_context = f"{user_message}\n\nUser context: {summary_context}"

    top_matches = vector_store.search(query_with_context, embed_func=embed_text, threshold=0.4)
    if not top_matches:
        msg = "❌ Couldn't find relevant knowledge — try rephrasing."
        await save_intent(user_uuid, session_id, user_message, msg, merged, db, intent="loan_rag")
        return {"response": msg, "mode": "rag"}

    top_q, top_a, _ = top_matches[0]
    kb_context = f"📚 Knowledge Match:\nQ: {top_q}\nA: {top_a}\n\n"

    try:
        web_query = openai_client.generate_response(f"Write a web search query to help answer this:\n{user_message}")
        search_results = serper_client.search(web_query)
        top_links = [item["link"] for item in search_results.get("organic", [])[:3]]
        web_summary = openai_client.generate_response(
            f"Summarize the content of these links:\n" + "\n".join(top_links)
        ) if top_links else ""
    except Exception as e:
        print("⚠️ Web augmentation failed:", e)
        web_summary = ""

    prompt = (
        f"User Query: {user_message}\n\n"
        f"User Context: {summary_context}\n\n"
        f"{kb_context}🔗 Web Info:\n{web_summary}\n\n"
        f"🎯 Provide a short, clear, and helpful response specific to Indian loan providers."
    )
    final_answer = openai_client.generate_response(prompt)

    if not final_answer.strip().startswith(("❌", "📍", "💰", "🗓️", "🙋‍♂️", "👋", "Sorry", "✅")):
        final_answer += "\n\n🤖 Let me know what more I can do to help you."

    await save_intent(user_uuid, session_id, user_message, final_answer, merged, db, intent="loan_rag")
    return {"response": final_answer, "mode": "rag"}

@router.get("/chats/resume")
async def resume_chat(
    session_id: str = Header(..., convert_underscores=False),
    db: AsyncSession = Depends(get_db)
):
    history = (await db.execute(select(Intent).where(Intent.session_id == session_id))).scalars().all()
    context = (await db.execute(
        select(Intent.context).where(Intent.session_id == session_id).order_by(Intent.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    return {
        "history": [intent.__dict__ for intent in history],
        "context": context
    }

async def save_intent(
    user_uuid: UUID,
    session_id: str,
    user_message: str,
    bot_response: str,
    parameters: dict,
    db: AsyncSession,
    intent: str = "loan_inquiry"
):
    description = ""
    if parameters:
        desc_parts = []
        for k in ["loan_type", "location", "income", "timeline", "loan_amount"]:
            if k in parameters:
                desc_parts.append(f"{k}: {parameters[k]}")
        description = ", ".join(desc_parts)

    new_intent = Intent(
        user_uuid=user_uuid,
        session_id=session_id,
        user_message=user_message,
        bot_response=bot_response,
        intent=intent,
        parameters=parameters,
        context={"summary": f"user needs: {parameters}"},
        created_at=datetime.utcnow(),
        name=parameters.get("name"),
        description=description,
        loan_type=parameters.get("loan_type"),
        last_user_query=parameters.get("last_user_query")
    )
    db.add(new_intent)
    await db.commit()
    await db.refresh(new_intent)
