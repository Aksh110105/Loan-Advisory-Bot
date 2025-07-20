import os
import re
import json
from typing import Optional, Dict
from openai import OpenAI, OpenAIError

MODEL_CHOICES = {
    "GPT-3.5 Turbo": "gpt-3.5-turbo",
    "GPT-4": "gpt-4",
    "GPT-4o": "gpt-4o"
}

EXIT_PHRASES = {
    "ok", "okay", "thanks", "thank you", "got it", "bye", "cool",
    "okay thanks", "i got it", "no more questions", "alright", "fine", "that's all"
}

class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ OPENAI_API_KEY not set.")
        self.client = OpenAI(api_key=self.api_key)
        self.model = MODEL_CHOICES["GPT-4"]

    def set_model(self, model_display_name: str):
        normalized_name = model_display_name.strip().lower()
        for name, internal_model in MODEL_CHOICES.items():
            if name.lower() == normalized_name or internal_model == normalized_name:
                self.model = internal_model
                return
        raise ValueError(f"⚠️ Invalid model name: {model_display_name}")

    def generate_response(self, message: str) -> str:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": message}],
                temperature=0.7
            )
            return completion.choices[0].message.content.strip()
        except OpenAIError as e:
            print(f"⚠️ OpenAI API Error: {e}")
            raise RuntimeError("⚠️ Failed to get response from OpenAI.")

    def is_loan_related(self, message: str) -> bool:
        prompt = (
            "You are a strict classifier. Only respond with 'yes' or 'no'.\n"
            "Determine if the query is strictly about one of the following loan types:\n"
            "- personal loan\n- home loan\n- education loan\n- vehicle loan\n- business loan\n- MSME loan\n\n"
            "If it's any other type (e.g., car wash, cosmetic, travel, wedding), respond 'no'.\n"
            f"User query: {message}"
        )
        try:
            answer = self.generate_response(prompt).lower().strip().strip(".?!")
            return answer == "yes"
        except Exception as e:
            print(f"⚠️ Loan intent classification failed: {e}")
            return False

    def is_greeting(self, message: str) -> bool:
        prompt = (
            "You're a classifier. Respond only with 'yes' or 'no'.\n"
            "Does this message look like a general greeting (e.g., hi, hello, hey, good morning, etc)?\n"
            f"Message: {message}"
        )
        try:
            answer = self.generate_response(prompt).lower().strip().strip(".?!")
            return answer == "yes"
        except Exception as e:
            print(f"⚠️ Greeting classification failed: {e}")
            return False

    def is_exit(self, message: str, full_context: str = "") -> bool:
        if message.strip().lower() in EXIT_PHRASES:
            print("🧠 Exact exit phrase match.")
            return True

        prompt = (
            f"The user sent this message: '{message}'\n\n"
            f"The chat so far:\n{full_context}\n\n"
            "Does this message politely indicate the user is ending the conversation?\n"
            "Reply with only 'yes' or 'no'."
        )
        try:
            answer = self.generate_response(prompt).lower().strip().strip(".?!")
            return answer == "yes"
        except Exception as e:
            print(f"⚠️ Exit classification failed: {e}")
            return False

    def extract_parameters(self, message: str) -> Dict[str, Optional[str]]:
        prompt = (
            "Extract loan-related details from the user's message.\n"
            "Respond with ONLY a valid JSON object with these fields:\n"
            "- location: city or state\n"
            "- income: monthly income (like 1 lakh, 50000, etc.)\n"
            "- timeline: when they plan to take the loan\n"
            "If any value is not found, return it as null.\n\n"
            f"User message: \"{message}\"\n\n"
            "Output:\n{\"location\": ..., \"income\": ..., \"timeline\": ...}"
        )
        try:
            response = self.generate_response(prompt)
            print("🔍 OpenAI raw response:", response)

            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r"^```(?:json)?\n?", "", response)
                response = re.sub(r"\n?```$", "", response)

            json_like = re.search(r'\{.*?\}', response, re.DOTALL)
            if not json_like:
                raise ValueError("OpenAI did not return valid JSON format.")

            fixed_json = json_like.group().replace("'", '"').replace("\\", "")
            parsed = json.loads(fixed_json)

            for key in ["location", "income", "timeline"]:
                if key not in parsed:
                    parsed[key] = None

            if parsed.get("income"):
                parsed["income"] = self._normalize_income(parsed["income"])
            elif parsed.get("income") is None:
                parsed["income"] = self._normalize_income(message)

            return parsed
        except Exception as e:
            print(f"⚠️ Failed to extract JSON from OpenAI: {e}")
            return {}

    def _normalize_income(self, income_str: str) -> Optional[int]:
        try:
            income_str = income_str.lower().replace(",", "").replace("₹", "").replace("rs", "").strip()
            if "lakh" in income_str:
                num = float(re.search(r"[\d.]+", income_str).group())
                return int(num * 100000)
            elif "k" in income_str:
                num = float(re.search(r"[\d.]+", income_str).group())
                return int(num * 1000)
            elif income_str.replace(".", "", 1).isdigit():
                return int(float(income_str))
        except Exception as e:
            print(f"⚠️ Failed to normalize income: {e}")
        return None
