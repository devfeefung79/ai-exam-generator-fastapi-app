import enum

from pydantic import BaseModel


class FileMetadata(BaseModel):
    filename: str
    path: str
    size_kb: float

class InputFileType(str, enum.Enum):
    DOCX = "docx"
    PDF = "pdf"
    TEXT = "txt"

class OutputFileType(str, enum.Enum):
    DOC = "doc"
    TEXT = "txt"