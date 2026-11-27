from typing import Literal

from pydantic import BaseModel, Field, model_validator

PlaceType = Literal[
    "street",
    "station",
    "district",
    "landmark",
    "geographical_location",
]

PlaceSource = Literal[
    "video_description",
    "voice_to_text",
    "hasthag_names",
    "ocr",
]


class PlaceMention(BaseModel):
    """Einzelne erkannte Ortsangabe."""

    text: str
    normalized_name: str
    type: PlaceType

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    detected_by: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    fuzzy_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    source: PlaceSource

    @model_validator(mode="after")
    def validate_positions(self):
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class IntersectionRelation(BaseModel):
    """Beziehung zwischen zwei Straßen an einer Kreuzung."""

    street1: str
    street2: str

    street1_start: int = Field(ge=0)
    street1_end: int = Field(ge=0)

    street2_start: int = Field(ge=0)
    street2_end: int = Field(ge=0)

    connector: Literal["und", "/", "&"]

    start: int = Field(ge=0)
    end: int = Field(ge=0)

    detected_by: list[str] = Field(default_factory=lambda: ["regex"])
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_positions(self):
        if self.street1_end <= self.street1_start:
            raise ValueError("street1_end must be greater than street1_start")

        if self.street2_end <= self.street2_start:
            raise ValueError("street2_end must be greater than street2_start")

        if self.end <= self.start:
            raise ValueError("end must be greater than start")

        return self


class PlaceExtractionResult(BaseModel):
    """Gesamtergebnis der Orts- und Beziehungserkennung."""

    places: list[PlaceMention] = Field(default_factory=list)
    relations: list[IntersectionRelation] = Field(default_factory=list)
