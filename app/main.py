import json
from typing import Optional
from datetime import datetime, timezone

import logging
from fastapi import FastAPI, Query, HTTPException, status, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from app.schemas.exam import Exam
from app.schemas.file import InputFileType, OutputFileType
from app.services.file_service import FileService
from app.services.gemini_service import GeminiService

app = FastAPI(
    title="Exam Generator API",
    description="API for generating mock exams using Google Gemini.",
    version="1.0.0"
)

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://ai-exam-generator-react-app.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

try:
    gemini_service = GeminiService()
except ValueError as e:
    print(f"FATAL ERROR: {e}")
    exit(1)

@app.post("/v1/exams/generate",
    response_model=Exam,
    status_code=status.HTTP_200_OK,
    summary="Generate a mock exam",
    description="Generates a mock exam with a specified number of questions, difficulty, and question types, based on an exam guide.")
async def generate_exam(
    num_questions: int = Form(...),
    difficulty: str = Form(...),
    question_types: str = Form(...),
    exam_guide_content: str = Form(""),
    additional_info: str = Form(""),
    exam_guide_file: Optional[UploadFile] = File(None)
) -> Exam:
    try:
        parsed_question_types = json.loads(question_types)

        if not exam_guide_content and not exam_guide_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'exam_guide_content' or 'exam_guide_file' must be provided."
            )

        if exam_guide_content and exam_guide_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either 'exam_guide_content' OR 'exam_guide_file', not both."
            )

        final_content = exam_guide_content  # Default to text content

        if exam_guide_file:
            if not exam_guide_file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must have a filename with extension."
                )

            filename_lower = exam_guide_file.filename.lower()

            supported_extensions = [filetype.value for filetype in InputFileType]

            if not any(filename_lower.endswith(f".{ext}") for ext in supported_extensions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type. Supported: {supported_extensions}"
                )

            try:
                final_content = await FileService.read_file(file=exam_guide_file)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error reading file: {str(e)}"
                )

        if not final_content or not final_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content found to generate exam from."
            )

        # Call the GeminiService to generate the exam content
        gemini_response = gemini_service.generate_exam(
            number_of_questions=num_questions,
            difficulty=difficulty,
            question_types=parsed_question_types,
            exam_guide=final_content,
            additional_info=additional_info
        )

        # The `gemini_response.parsed` attribute holds the Python object
        # that results from parsing the JSON response, which should conform
        # to your `Exam` Pydantic model due to the `response_schema` in GeminiService.
        if not gemini_response.parsed:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API returned an empty or unparseable response."
            )

        # Validate the parsed response against the Exam Pydantic model.
        # This adds an extra layer of safety to ensure the structure is correct
        # before returning it. If the structure doesn't match, Pydantic will raise a ValidationError.
        generated_exam = Exam.model_validate(gemini_response.parsed)

        return generated_exam

    except RuntimeError as e:
        # Catch specific RuntimeErrors raised by GeminiService (e.g., API call failures)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating exam from Gemini: {e}"
        )
    except Exception as e:
        print(f"Full exception details: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        # Catch any other unexpected errors during the process
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the request: {e}"
        )

@app.post("/v1/exams/download", response_class=StreamingResponse)
def download_exam(exam: Exam, file_type: str = Query(...)):
    if file_type not in [ft.value for ft in OutputFileType]:
        raise HTTPException(status_code=400, detail="Invalid file type")


    return FileService.create_file_stream(exam, file_type)
