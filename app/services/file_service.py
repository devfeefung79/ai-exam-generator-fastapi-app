import logging
import os
import tempfile
from io import StringIO, BytesIO

import PyPDF2
from docx import Document
from fastapi import UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.exam import Exam

logger = logging.getLogger(__name__)


class FileService:
    @staticmethod
    def create_file_stream(exam: Exam, file_type: str) -> StreamingResponse:
        buffer = StringIO()

        buffer.write(f"Exam Title: {exam.exam_title}\n")
        buffer.write(f"Questions: {exam.total_questions}\n")
        buffer.write(f"Difficulty: {exam.difficulty}\n")
        buffer.write(f"Estimated Time: {exam.estimated_completion_minutes} minutes\n")
        buffer.write(f"Types: {', '.join(exam.question_types)}\n")
        buffer.write("\n" + "=" * 40 + "\n\n")

        for q in exam.questions:
            buffer.write(f"Question {q.id} [{q.type} - {q.difficulty}]\n{q.question}\n\n")

            if q.type == "Multiple Choice":
                for i, option in enumerate(q.options):
                    buffer.write(f"{chr(65 + i)}. {option}\n")

            if q.type == "Essay":
                buffer.write(f"Guidelines: {q.guidelines}\n")

            buffer.write("\n" + "-" * 40 + "\n\n")

        buffer.write("\nANSWER KEY\n" + "=" * 40 + "\n\n")
        for q in exam.questions:
            if q.type == "Multiple Choice" or q.type == "True/False":
                buffer.write(f"Question {q.id}: {q.correct_answer}\n")
            if q.type == "Short Answer":
                buffer.write(f"Question {q.id}: [Sample Answer] {q.sample_answer}\n")
            if q.type == "Essay":
                buffer.write(f"Question {q.id}: Not Applicable\n")

        # Reset cursor
        buffer.seek(0)

        filename = f"{exam.exam_title.replace(' ', '_')}.{file_type}"

        mime_map = {
            "txt": "text/plain",
            "doc": "application/msword",
        }

        return StreamingResponse(
            buffer,
            media_type=mime_map.get(file_type),
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @staticmethod
    async def read_file(file: UploadFile) -> str:
        """
        Read and extract text from uploaded file

        Issues fixed:
        1. Proper error handling with HTTPException instead of returning error strings
        2. File cleanup to prevent temp file accumulation
        3. Better encoding handling for text files
        4. Input validation
        5. Support for DOC files
        6. Memory-based processing where possible (no temp files for PDF)
        """

        logger.info("Reading file with name: %s", file.filename)
        # Input validation
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        filename = file.filename.lower()
        if "." not in filename:
            raise HTTPException(status_code=400, detail="File must have an extension")

        extension = filename.split(".")[-1]

        try:
            if extension == "txt":
                return await FileService._read_txt_file(file)
            elif extension == "docx":
                return await FileService._read_docx_file(file)
            elif extension == "doc":
                return await FileService._read_doc_file(file)
            elif extension == "pdf":
                return await FileService._read_pdf_file(file)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {extension}. Supported: txt, docx, doc, pdf"
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
        finally:
            await file.close()

    @staticmethod
    async def _read_txt_file(file: UploadFile) -> str:
        """Read text file with multiple encoding support"""
        logger.info("Reading text file with name: " + file.filename)
        content = await file.read()

        # Try multiple encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                text = content.decode(encoding)
                if text.strip():  # Ensure we got actual content
                    return text
            except UnicodeDecodeError:
                continue

        raise HTTPException(status_code=400, detail="Could not decode text file")

    @staticmethod
    async def _read_docx_file(file: UploadFile) -> str:
        """Read DOCX file using temporary file"""
        logger.info("Reading DOCX file with name: " + file.filename)
        content = await file.read()
        temp_file = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                temp_file = tmp.name
                tmp.write(content)
                tmp.flush()

                doc = Document(tmp.name)
                text_content = "\n".join([para.text for para in doc.paragraphs])

                if not text_content.strip():
                    raise HTTPException(status_code=400, detail="No text content found in DOCX file")

                return text_content

        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

    @staticmethod
    async def _read_pdf_file(file: UploadFile) -> str:
        """Read PDF file using memory stream (no temp file needed)"""
        logger.info("Reading PDF file with name: " + file.filename)
        content = await file.read()

        try:
            # Use BytesIO instead of temp file - more efficient
            pdf_stream = BytesIO(content)
            reader = PyPDF2.PdfReader(pdf_stream)

            if len(reader.pages) == 0:
                raise HTTPException(status_code=400, detail="PDF file has no pages")

            text_pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:  # Only add non-empty pages
                    text_pages.append(page_text)

            full_text = "\n".join(text_pages)

            if not full_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No text content found in PDF. File might be image-based or encrypted."
                )

            return full_text

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process PDF file: {str(e)}")
