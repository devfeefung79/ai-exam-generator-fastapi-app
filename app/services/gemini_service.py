import os
from datetime import datetime, timezone
import logging

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from google.genai.types import GenerateContentResponse

from app.schemas.exam import Exam

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Configure logging
        self.service_name = "GeminiService"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Get API key
        self.api_key = os.getenv("GOOGLE_API_KEY") # Use GOOGLE_API_KEY for genai client default behavior
        if not self.api_key:
            raise ValueError("Google API key (GOOGLE_API_KEY) is not set. Please set it in your environment or .env file.")

        # Explicitly pass the API key to the client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name

    @staticmethod
    def build_prompt(num_questions: int, difficulty: str, question_types: list, exam_guide: str, additional_info: str) -> str:
        return (
            f"Given the following exam guide content, generate mock exam questions (see specifications below) with answers. \n"
            f"- total number of questions: {num_questions} \n"
            f"- difficulty level: {difficulty} \n"
            f"- question types: {', '.join(question_type for question_type in question_types)} \n"
            f"- output format: JSON \n\n"
            f"- exam guide: {exam_guide} \n"
            f"- additional information: {additional_info} \n\n"
            f"Please ensure the output is a valid JSON object strictly conforming to the provided schema."
        )

    def generate_exam(self, number_of_questions: int, difficulty: str, question_types: list, exam_guide: str, additional_info: str) -> GenerateContentResponse:
        try:
            prompt = self.build_prompt(number_of_questions, difficulty, question_types, exam_guide, additional_info)

            response = self.client.models.generate_content(model=self.model_name,
                                                           contents=prompt,
                                                           config={
                                                               "response_mime_type": "application/json",
                                                               "response_schema": Exam,
                                                           })

            return response

        except APIError as e:
            raise RuntimeError(f"Gemini API error occurred (status {e.code}): {e.message}") from e

        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during Gemini API call: {e}") from e
