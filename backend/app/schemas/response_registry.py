from __future__ import annotations

from typing import Dict, Any

from app.schemas.wizard import (
    Text,
	WorldBuilding, Blueprint,
	VolumeOutline, ChapterOutline,
	SpecialAbilityResponse, OneSentence, ParagraphOverview,
	CharacterCard, SceneCard, StoryLine, StageLine,
	Tags, WorldviewTemplate, Chapter,
 WritingGuide, ReviewResultCardContent
)
from app.schemas.entity import ConceptCard, ItemCard, OrganizationCard
from app.schemas.workflow_models import BookStageChunkPlan, BookStageFinalPlan


RESPONSE_MODEL_MAP: Dict[str, Any] = {
    "Text": Text,
	'Tags': Tags,
	'SpecialAbilityResponse': SpecialAbilityResponse,
	'OneSentence': OneSentence,
	'ParagraphOverview': ParagraphOverview,
	'WorldBuilding': WorldBuilding,
	'WorldviewTemplate': WorldviewTemplate,
	'Blueprint': Blueprint,
	'VolumeOutline': VolumeOutline,
 	'WritingGuide': WritingGuide,
    'ReviewResultCardContent': ReviewResultCardContent,
	'ChapterOutline': ChapterOutline,
	'Chapter': Chapter,
	'CharacterCard': CharacterCard,
	'SceneCard': SceneCard,
	'OrganizationCard': OrganizationCard,
	'ItemCard': ItemCard,
	'ConceptCard': ConceptCard,
	'StageLine': StageLine,
	'StoryLine': StoryLine,
	'BookStageChunkPlan': BookStageChunkPlan,
	'BookStageFinalPlan': BookStageFinalPlan,
}
