from typing import List, Optional
from pydantic import BaseModel, Field


class Character(BaseModel):
    character_id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    age: Optional[int] = None
    role: Optional[str] = None
    relationships: List[str] = Field(default_factory=list)
    personality: List[str] = Field(default_factory=list)
    dialect: Optional[str] = None
    emotional_state: Optional[str] = None
    costume_id: Optional[str] = None


class Costume(BaseModel):
    costume_id: str
    name: str
    garments: List[str] = Field(default_factory=list)
    fabrics: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    footwear: List[str] = Field(default_factory=list)
    jewellery: List[str] = Field(default_factory=list)
    headwear: List[str] = Field(default_factory=list)
    grooming: List[str] = Field(default_factory=list)
    scene_ids: List[str] = Field(default_factory=list)


class Prop(BaseModel):
    prop_id: str
    name: str
    description: Optional[str] = None


class Scene(BaseModel):
    scene_id: str
    location_id: str
    interior_exterior: Optional[str] = None
    time: Optional[str] = None
    weather: Optional[str] = None
    mood: Optional[str] = None
    summary: str
    dramatic_purpose: Optional[str] = None
    character_ids: List[str] = Field(default_factory=list)
    costume_ids: List[str] = Field(default_factory=list)
    prop_ids: List[str] = Field(default_factory=list)
    props_in: List[str] = Field(default_factory=list)
    props_out: List[str] = Field(default_factory=list)
    emotional_changes: List[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    title: str
    characters: List[Character] = Field(default_factory=list)
    costumes: List[Costume] = Field(default_factory=list)
    props: List[Prop] = Field(default_factory=list)
    scenes: List[Scene] = Field(default_factory=list)


class CulturalDecision(BaseModel):
    category: str
    source_element: str
    adapted_element: str
    reason: str
    confidence: float = Field(ge=0, le=1)
    requires_review: bool = False


class AdaptationPlan(BaseModel):
    culture: str
    dialect: str
    region: str
    setting: str
    output_script: str
    output_language: Optional[str] = "Hindi"
    decisions: List[CulturalDecision] = Field(default_factory=list)
