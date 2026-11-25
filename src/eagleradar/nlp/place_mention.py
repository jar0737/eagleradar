from typing import Literal

from pydantic import BaseModel, Field, model_validator


# Orts Datenobjekt
class PlaceMention(BaseModel):
    text: str
    normalized_name: str
    type: Literal[
        "street", "station", "district", "landmark", "geographical_location", "intersection"
    ]
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    detected_by: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["video_description", "voice_to_text", "hasthag_names", "ocr"]

    @model_validator(mode="after")
    def validate_positions(self):
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self
