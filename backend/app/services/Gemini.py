import os
import json
import re
import google.generativeai as genai
from typing import Optional, Dict

MODEL_CHOICES = {
    "Gemini 1.5 Flash": "gemini-1.5-flash",
    "Gemini 1.5 Flash Latest": "gemini-1.5-flash-latest",
    "Gemini 2.5 Flash Preview (May 20)": "gemini-2.5-flash-preview-05-20",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 1.5 Pro": "gemini-1.5-pro",
    "Gemini 2.5 Pro Preview (June 5)": "gemini-2.5-pro-preview-06-05"
}

class GeminiClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not set.")
        genai.configure(api_key=self.api_key)
        self.model = None

    def set_model(self, model_display_name: str):
        if model_display_name in MODEL_CHOICES:
            self.model = genai.GenerativeModel(MODEL_CHOICES[model_display_name])
        else:
            raise ValueError(f"⚠️ Invalid model name: {model_display_name}")

    def generate_response(self, message: str) -> str:
        if not self.model:
            raise ValueError("⚠️ Model not set. Call set_model() first.")
        try:
            response = self.model.generate_content(message)
            return response.text.strip()
        except Exception as e:
            error_message = str(e)
            print(f"⚠️ Gemini API Error: {error_message}")
            if "429" in error_message or "quota" in error_message.lower():
                raise RuntimeError("🚫 Gemini API quota exceeded.")
            raise RuntimeError("⚠️ Failed to get response from Gemini.")

    def is_loan_related(self, message: str) -> bool:
        prompt = (
            "Respond only with 'yes' or 'no'.\n"
            "Does this query express interest in personal, home, or education loans?\n"
            "Avoid false positives. Only respond 'yes' if the user seems genuinely interested in loans.\n\n"
            f"Query: {message}"
        )
        try:
            answer = self.generate_response(prompt).lower().strip().strip(".?!")
            return answer == "yes"
        except Exception as e:
            print(f"⚠️ Loan intent classification failed: {e}")
            return False

    def extract_parameters(self, message: str) -> Dict[str, Optional[str]]:
        prompt = (
            "Extract loan-related details from the user's message.\n"
            "Respond with ONLY a valid JSON object with these fields:\n"
            "- location: city or state\n"
            "- income: monthly income (like 1 lakh, 50000, etc.)\n"
            "- timeline: when they plan to take the loan\n"
            "If any value is not found, return it as null.\n\n"
            "Examples:\n"
            "Input: I earn ₹2.5 lakh per month in Delhi and want a loan next year\n"
            "Output: {\"location\": \"Delhi\", \"income\": \"2.5 lakh\", \"timeline\": \"next year\"}\n"
            "Input: I need a loan this month. My salary is Rs 50000 and I live in Mumbai\n"
            "Output: {\"location\": \"Mumbai\", \"income\": \"50000\", \"timeline\": \"this month\"}\n\n"
            f"User message: \"{message}\"\n\n"
            "Output:\n{\"location\": ..., \"income\": ..., \"timeline\": ...}"
        )
        try:
            response = self.generate_response(prompt)
            print("🔍 Gemini raw response:", response)

            response = response.strip()
            if response.startswith("```"):
                response = re.sub(r"^```(?:json)?\n?", "", response)
                response = re.sub(r"\n?```$", "", response)

            json_like = re.search(r'\{.*?\}', response, re.DOTALL)
            if not json_like:
                raise ValueError("Gemini did not return valid JSON format.")

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
            print(f"⚠️ Failed to extract JSON from Gemini: {e}")
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
