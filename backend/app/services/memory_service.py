from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from sqlmodel import Session
from sqlalchemy.orm.attributes import flag_modified

from loguru import logger

from app.schemas.relation_extract import RelationExtraction, CN_TO_EN_KIND
from app.schemas.entity import Entity
from app.services.ai.core import llm_service
from pydantic import BaseModel
# å¼•å…¥åŠ¨æ€ä¿¡æ¯æ¨¡åž‹
from app.schemas.entity import UpdateDynamicInfo, DynamicInfoType, DynamicInfoItem, DeletionInfo
from app.db.models import Card, CardType
from sqlmodel import select

# å¼•å…¥å¸¦ç±»åž‹çš„å‚ä¸Žè€…æ¨¡åž‹
from app.schemas.memory import ParticipantTyped

# ä»Žæ•°æ®åº“åŠ è½½æç¤ºè¯
from app.services import prompt_service
from app.services.memory_extractors.memory_base import log_extract_prompt
from app.services.memory_extractors.registry_factory import get_memory_extractor_registry
from app.services.card_type_service_utils import resolve_card_type_key

# ä½¿ç”¨å¯åˆ‡æ¢çš„çŸ¥è¯†å›¾è°± Provider
from app.services.kg_provider import get_provider, KnowledgeGraphUnavailableError


def _card_type_key(card_type: Optional[CardType]) -> Optional[str]:
    if not card_type:
        return None
    return getattr(card_type, 'key', None) or resolve_card_type_key(getattr(card_type, 'name', None))

# ä¸»å®¾ç±»åž‹çº¦æŸï¼ˆå»ºè®®è¡¨ï¼‰
_ALLOWED_PAIRS: Dict[str, List[Tuple[str, str]]] = {
    'åŒç›Ÿ': [('character','character')],
    'é˜Ÿå‹': [('character','character')],
    'åŒé—¨': [('character','character')],
    'æ•Œå¯¹': [('character','character')],
    'äº²å±ž': [('character','character')],
    'å¸ˆå¾’': [('character','character')],
    'å¯¹æ‰‹': [('character','character')],
    'ä¼™ä¼´': [('character','character')],
    'ä¸Šçº§': [('character','character')],
    'ä¸‹å±ž': [('character','character')],

    'éš¶å±ž': [('character','organization')],
    'æˆå‘˜': [('character','organization')],
    'é¢†å¯¼': [('character','organization'), ('organization','organization')],
    'åˆ›ç«‹': [('character','organization') , ('organization','organization')],

    'æ‹¥æœ‰': [('character','item'), ('organization','item')],
    'ä½¿ç”¨': [('character','item'), ('organization','item')],
    'ä¿®ç‚¼': [('character','concept')],
    'é¢†æ‚Ÿ': [('character','concept')],
    'æ‰¿è½½': [('item','concept')],
    'æ˜ å°„': [('concept','item')],

    'æŽ§åˆ¶': [('organization','scene')],
    'ä½äºŽ': [('scene','organization')],

    
    'å…³äºŽ': [('character','character'), ('organization','organization'), ('character','organization'), ('organization','character'),
        #    ('item','item'), ('concept','concept'), ('character','concept'), ('character','item')
           ],
    'å…¶ä»–': [('character','character'), ('organization','organization'), ('character','organization'), ('organization','character'), ('item','item'), ('concept','concept'), ('character','concept'), ('character','item')],
    # 'å½±å“': [('character','character'), ('organization','organization'), ('character','organization'), ('organization','character'), ('item','item'), ('concept','concept'), ('character','concept'), ('character','item'), ('scene','organization'), ('organization','scene')],
    # 'å…‹åˆ¶': [('item','item'), ('concept','concept'), ('character','character')],
}

# # ç®€åŒ–ï¼šä»Žå¡ç‰‡ç±»åž‹åç§°æŽ¨æ–­å®žä½“ç±»åž‹
# _CARDTYPE_TO_ENTITYTYPE: Dict[str, str] = {
#     'è§’è‰²å¡': 'character',
#     'åœºæ™¯å¡': 'scene',
#     'ç»„ç»‡å¡': 'organization',
#     # 'ç‰©å“å¡': 'item',
#     # 'æ¦‚å¿µå¡': 'concept',
# }

def _guess_entity_type(session: Session, project_id: int, name: str) -> Optional[str]:
    try:
        # åœ¨è¯¥é¡¹ç›®ä¸‹æŸ¥æ‰¾ title == name çš„å¡ç‰‡ï¼Œå¹¶è¯»å–å…¶ç±»åž‹åç§°
        st = select(Card).where(Card.project_id == project_id, Card.title == name)
        card = session.exec(st).first()
        if not card:
            return None
        ct = card.card_type
        if not ct:
            return None
        
        # ä¿®æ­£ï¼šcard.content å·²ç»æ˜¯ dictï¼Œåº”ä½¿ç”¨ model_validate è€Œä¸æ˜¯ model_validate_json
        entity=Entity.model_validate(card.content)
        return str(entity.entity_type)
        # return _CARDTYPE_TO_ENTITYTYPE.get(ct.name or '', None)
    except Exception as e:
        logger.error(f"Error guessing entity type: {e}")
        return None


# åŠ¨æ€ä¿¡æ¯æ¯ç±»åˆ«æ•°é‡ä¸Šé™ï¼ˆå¯æ ¹æ®éœ€è¦è°ƒæ•´ï¼‰
DYNAMIC_INFO_LIMITS: Dict[str, int] = {
    "ç³»ç»Ÿ/æ¨¡æ‹Ÿå™¨/é‡‘æ‰‹æŒ‡ä¿¡æ¯": 3,
    "ç­‰çº§/ä¿®ä¸ºå¢ƒç•Œ": 3,
    "è£…å¤‡/æ³•å®": 3,
    "çŸ¥è¯†/æƒ…æŠ¥": 3,
    "èµ„äº§/é¢†åœ°": 3,
    "åŠŸæ³•/æŠ€èƒ½": 3,
    "è¡€è„‰/ä½“è´¨": 3,
    "å¿ƒç†æƒ³æ³•/ç›®æ ‡å¿«ç…§": 3,
}

class MemoryService:
    def __init__(self, session: Session):
        self.session = session
        self.graph = get_provider()
        self.extractor_registry = get_memory_extractor_registry()

    def list_extractors(self) -> List[Dict[str, Any]]:
        return [
            {
                "code": extractor.code,
                "name": extractor.name,
                "target": extractor.target,
                "preview_supported": extractor.preview_supported,
            }
            for extractor in self.extractor_registry.list_all()
        ]

    async def extract_preview(
        self,
        *,
        extractor_code: str,
        project_id: int | None,
        text: str,
        participants: Optional[List[ParticipantTyped]] = None,
        llm_config_id: int = 1,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        extra_context: Optional[str] = None,
        volume_number: Optional[int] = None,
        chapter_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        extractor = self.extractor_registry.get(extractor_code)
        typed_participants = participants or []
        data = await extractor.extract(
            service=self,
            session=self.session,
            project_id=project_id,
            text=text,
            participants=typed_participants,
            llm_config_id=llm_config_id,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            extra_context=extra_context,
            context={
                "volume_number": volume_number,
                "chapter_number": chapter_number,
            },
        )
        return {
            "extractor_code": extractor.code,
            "preview_data": data.model_dump(mode="json"),
            "affected_targets": extractor.build_affected_targets(data),
        }

    def apply_preview(
        self,
        *,
        extractor_code: str,
        project_id: int,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        volume_number: Optional[int] = None,
        chapter_number: Optional[int] = None,
        participants: Optional[List[ParticipantTyped]] = None,
    ) -> Dict[str, Any]:
        extractor = self.extractor_registry.get(extractor_code)
        preview_data = extractor.output_model.model_validate(data)
        result = extractor.persist(
            service=self,
            session=self.session,
            project_id=project_id,
            data=preview_data,
            options=options,
            context={
                "volume_number": volume_number,
                "chapter_number": chapter_number,
                "participants": participants or [],
            },
        )
        return {
            "success": True,
            "written": int(result.get("written", 0)),
            "updated_card_count": int(result.get("updated_card_count", 0)),
            "updated_relation_count": int(
                result.get("updated_relation_count", result.get("written", 0) if extractor.target == "graph" else 0)
            ),
            "affected_targets": extractor.build_affected_targets(preview_data),
            "raw_result": result,
        }

    async def extract_relations_preview(
        self,
        *,
        text: str,
        participants: Optional[List[ParticipantTyped]] = None,
        llm_config_id: int = 1,
        timeout: Optional[float] = None,
        prompt_name: Optional[str] = "relationship_extraction",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> RelationExtraction:
        prompt = prompt_service.get_prompt_by_identifier(self.session, prompt_name)
        system_prompt = prompt.template

        schema_json = RelationExtraction.model_json_schema()
        system_prompt += f"\n\nè¯·ä¸¥æ ¼æŒ‰ä»¥ä¸‹ JSON Schema æ ¼å¼è¾“å‡º:\n{schema_json}"

        participant_names = [p.name for p in participants] if participants else []
        user_prompt = (
            f"å‚ä¸Žè€…: {', '.join(participant_names)}\n\n"
            "è¯·ä»Žä»¥ä¸‹æ­£æ–‡ä¸­æå–:\n"
            f"{text}"
        )
        log_extract_prompt("relation_preview", prompt_name, llm_config_id, system_prompt, user_prompt)
        res = await llm_service.generate_structured(
            session=self.session,
            llm_config_id=llm_config_id,
            user_prompt=user_prompt,
            output_type=RelationExtraction,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        if not isinstance(res, RelationExtraction):
            raise ValueError("LLM å…³ç³»æŠ½å–å¤±è´¥ï¼šè¾“å‡ºæ ¼å¼ä¸ç¬¦åˆ RelationExtraction")
        return res

    async def extract_dynamic_info_preview(
        self,
        *,
        text: str,
        participants: Optional[List[ParticipantTyped]] = None,
        llm_config_id: int = 1,
        timeout: Optional[float] = None,
        prompt_name: Optional[str] = "character_dynamic_info_extraction",
        project_id: Optional[int] = None,
        extra_context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> UpdateDynamicInfo:
        prompt = prompt_service.get_prompt_by_identifier(self.session, prompt_name)
        if not prompt:
            raise ValueError(f"æœªæ‰¾åˆ°æç¤ºè¯: {prompt_name}")
        system_prompt = prompt.template

        schema_json = UpdateDynamicInfo.model_json_schema()
        system_prompt += f"\n\nè¯·ä¸¥æ ¼æŒ‰ä»¥ä¸‹ JSON Schema æ ¼å¼è¾“å‡º:\n{schema_json}"

        ref_blocks: List[str] = []
        if extra_context:
            ref_blocks.append(f"ã€å¤§çº²å‚è€ƒä¿¡æ¯ï¼Œä¸å…è®¸ä»Žä¸­æå–ä¿¡æ¯ã€‘\n{extra_context}")

        character_participants = [p for p in (participants or []) if p.type == 'character']
        if project_id and character_participants:
            try:
                lines: List[str] = []
                for p in character_participants:
                    st = select(Card).where(Card.project_id == project_id, Card.title == p.name)
                    card = self.session.exec(st).first()
                    if not card or not card.card_type or _card_type_key(card.card_type) != 'character_card':
                        continue
                    try:
                        from app.schemas.entity import CharacterCard

                        model = CharacterCard.model_validate(card.content or {})
                        di = model.dynamic_info or {}
                        if not di:
                            continue
                        lines.append(f"- {p.name}:")
                        for cat_enum, items in di.items():
                            if len(items) == 0:
                                continue
                            preview = "; ".join([f"[{it.id}] {it.info}" for it in items[:5]])
                            limit = DYNAMIC_INFO_LIMITS.get(cat_enum, 3)
                            info_line = f"  - {cat_enum} ({len(items)}/{limit}): {preview}"
                            lines.append(info_line)
                    except Exception as e:
                        logger.error(f"Error preparing dynamic info context: {e}")
                        continue
                if lines:
                    ref_blocks.append("ã€çŽ°æœ‰è§’è‰²åŠ¨æ€ä¿¡æ¯ï¼ˆåªè¯»å‚è€ƒï¼‰ã€‘\n" + "\n".join(lines))
            except Exception as e:
                logger.error(f"Error preparing dynamic info context: {e}")

        ref_text = ("\n\n".join(ref_blocks) + "\n\n") if ref_blocks else ""
        participant_text = ""
        if character_participants:
            participant_text = (
                "æœ¬ç« å½“å‰å‚ä¸Žè§’è‰²ï¼ˆä»…ä½œä¼˜å…ˆå‚è€ƒï¼Œä¸æ˜¯ç¡¬é™åˆ¶ï¼›å¦‚æžœæ­£æ–‡é‡Œæ˜Žç¡®å‡ºçŽ°äº†å…¶ä»–é‡è¦è§’è‰²ï¼Œä¹Ÿå¯ä»¥æå–ï¼‰ï¼š\n"
                f"{', '.join([p.name for p in character_participants])}\n\n"
            )
        user_prompt = (
            f"{ref_text}"
            f"ç« èŠ‚æ­£æ–‡:\n{text}\n\n"
            f"{participant_text}"
            "è¯·ä»Žä»¥ä¸Šæ­£æ–‡ä¸­æå–æœ¬ç« å€¼å¾—å†™å›žè§’è‰²å¡çš„åŠ¨æ€ä¿¡æ¯ã€‚"
        )

        log_extract_prompt("character_dynamic_preview", prompt_name, llm_config_id, system_prompt, user_prompt)
        res = await llm_service.generate_structured(
            session=self.session,
            llm_config_id=llm_config_id,
            user_prompt=user_prompt,
            output_type=UpdateDynamicInfo,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        if not isinstance(res, UpdateDynamicInfo):
            raise ValueError("LLM åŠ¨æ€ä¿¡æ¯æŠ½å–å¤±è´¥ï¼šè¾“å‡ºæ ¼å¼ä¸ç¬¦åˆ UpdateDynamicInfo")

        return res

    async def extract_relations_llm(self, text: str, participants: Optional[List[ParticipantTyped]] = None, llm_config_id: int = 1, timeout: Optional[float] = None, prompt_name: Optional[str] = "relationship_extraction") -> RelationExtraction:
        # ä¼˜å…ˆä½¿ç”¨é»˜è®¤æç¤ºè¯ï¼Œå¦‚æžœä¸å­˜åœ¨åˆ™å›žé€€åˆ°ç¡¬ç¼–ç ç‰ˆæœ¬
        prompt = prompt_service.get_prompt_by_identifier(self.session, prompt_name)
        system_prompt = prompt.template
        
        # å°†è¾“å‡ºæ¨¡åž‹çš„ JSON Schema é™„åŠ åˆ°ç³»ç»Ÿæç¤ºè¯ä¸­
        schema_json = RelationExtraction.model_json_schema()
        system_prompt += f"\n\nè¯·ä¸¥æ ¼æŒ‰ç…§ä»¥ä¸‹ JSON Schema æ ¼å¼è¿›è¡Œè¾“å‡º:\n{schema_json}"

        participant_names = [p.name for p in participants] if participants else []
        user_prompt = (
            f"å‚ä¸Žè€…: {', '.join(participant_names)}\n\n"
            "è¯·ä»Žä»¥ä¸‹æ­£æ–‡ä¸­æŠ½å–ï¼š\n"
            f"{text}"
        )
        log_extract_prompt("relation_extract", prompt_name, llm_config_id, system_prompt, user_prompt)
        res = await llm_service.generate_structured(
            session=self.session,
            llm_config_id=llm_config_id,
            user_prompt=user_prompt,
            output_type=RelationExtraction,
            system_prompt=system_prompt,
            timeout=timeout,
        )
        if not isinstance(res, RelationExtraction):
            raise ValueError("LLM å…³ç³»æŠ½å–å¤±è´¥ï¼šè¾“å‡ºæ ¼å¼ä¸ç¬¦åˆ RelationExtraction")
        return res

    async def extract_dynamic_info_from_text(self, text: str, participants: Optional[List[ParticipantTyped]] = None, llm_config_id: int = 1, timeout: Optional[float] = None, prompt_name: Optional[str] = "character_dynamic_info_extraction", project_id: Optional[int] = None, extra_context: Optional[str] = None) -> UpdateDynamicInfo:
        """ä»Žæ–‡æœ¬ä¸­æŠ½å–è§’è‰²åŠ¨æ€ä¿¡æ¯ã€‚participants ä»…ä½œä¸ºä¼˜å…ˆå‚è€ƒï¼Œä¸ä½œä¸ºç¡¬é™åˆ¶ã€‚"""
        prompt = prompt_service.get_prompt_by_identifier(self.session, prompt_name)
        if not prompt:
            raise ValueError(f"æœªæ‰¾åˆ°æç¤ºè¯: {prompt_name}")
        system_prompt = prompt.template

        # é™„åŠ  JSON Schema ä»¥å¼ºåŒ–è¾“å‡ºç»“æž„
        schema_json = UpdateDynamicInfo.model_json_schema()
        system_prompt += f"\n\nè¯·ä¸¥æ ¼æŒ‰ç…§ä»¥ä¸‹ JSON Schema æ ¼å¼è¿›è¡Œè¾“å‡º:\n{schema_json}"

        # å‚è€ƒä¸Šä¸‹æ–‡ï¼ˆå®Œå…¨ç”±å‰ç«¯å†³å®šï¼‰+ çŽ°æœ‰è§’è‰²åŠ¨æ€ä¿¡æ¯
        ref_blocks: List[str] = []
        if extra_context:
            ref_blocks.append(f"ã€å¤§çº²å‚è€ƒä¿¡æ¯ï¼Œä¸å…è®¸ä»Žä¸­æå–ä¿¡æ¯ã€‘\n{extra_context}")

        # ä½¿ç”¨å¸¦ç±»åž‹çš„å‚ä¸Žè€…ï¼Œä»…å¤„ç† character ç±»åž‹
        character_participants = [p for p in (participants or []) if p.type == 'character']
        if project_id and character_participants:
            try:
                lines: List[str] = []
                for p in character_participants:
                    st = select(Card).where(Card.project_id == project_id, Card.title == p.name)
                    card = self.session.exec(st).first()
                    if not card or not card.card_type or _card_type_key(card.card_type) != 'character_card':
                        continue
                    try:
                        from app.schemas.entity import CharacterCard
                     
                        model = CharacterCard.model_validate(card.content or {})
    
                        di = model.dynamic_info or {}
                        if not di:
                            continue
                        lines.append(f"- {p.name}:")
                        for cat_enum, items in di.items():
                            if len(items)==0:
                                continue

                            # å¢žåŠ æ•°é‡/ä¸Šé™çš„ä¸Šä¸‹æ–‡ï¼ˆåŽ»æŽ‰æƒé‡ï¼‰
                            preview = "; ".join([f"[{it.id}] {it.info}" for it in items[:5]])
                            limit = DYNAMIC_INFO_LIMITS.get(cat_enum, 3)
                            info_line = f"  â€¢ {cat_enum} ({len(items)}/{limit}): {preview}"
                            lines.append(info_line)
                    except Exception as e:
                        logger.error(f"Error preparing dynamic info context: {e}")
                        continue
                if lines:
                    ref_blocks.append("ã€çŽ°æœ‰è§’è‰²åŠ¨æ€ä¿¡æ¯ï¼ˆåªè¯»å‚è€ƒï¼‰ã€‘\n" + "\n".join(lines))
            except Exception as e:
                logger.error(f"Error preparing dynamic info context: {e}")

        ref_text = ("\n\n".join(ref_blocks) + "\n\n") if ref_blocks else ""
        participant_text = ""
        if character_participants:
            participant_text = (
                "æœ¬ç« å½“å‰å‚ä¸Žè§’è‰²ï¼ˆä»…ä½œä¼˜å…ˆå‚è€ƒï¼Œä¸æ˜¯ç¡¬é™åˆ¶ï¼›å¦‚æžœæ­£æ–‡é‡Œæ˜Žç¡®å‡ºçŽ°äº†å…¶ä»–é‡è¦è§’è‰²ï¼Œä¹Ÿå¯ä»¥æå–ï¼‰ï¼š\n"
                f"{', '.join([p.name for p in character_participants])}\n\n"
            )

        user_prompt = (
            f"{ref_text}"
            f"ç« èŠ‚æ­£æ–‡ï¼š\n{text}\n\n"
            f"{participant_text}"
            "è¯·ä»Žä»¥ä¸Šæ­£æ–‡ä¸­æå–æœ¬ç« å€¼å¾—å†™å›žè§’è‰²å¡çš„åŠ¨æ€ä¿¡æ¯ã€‚"
        )

        log_extract_prompt("character_dynamic_extract", prompt_name, llm_config_id, system_prompt, user_prompt)
        res = await llm_service.generate_structured(
            session=self.session,
            llm_config_id=llm_config_id,
            user_prompt=user_prompt,
            output_type=UpdateDynamicInfo,
            system_prompt=system_prompt,
            timeout=timeout,
        )

        if not isinstance(res, UpdateDynamicInfo):
            raise ValueError("LLM åŠ¨æ€ä¿¡æ¯æŠ½å–å¤±è´¥ï¼šè¾“å‡ºæ ¼å¼ä¸ç¬¦åˆ UpdateDynamicInfo")
        
        return res

    def query_subgraph(
        self,
        project_id: int,
        participants: Optional[List[str]] = None,
        radius: int = 2,
        edge_type_whitelist: Optional[List[str]] = None,
        top_k: int = 50,
        max_chapter_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self.graph.query_subgraph(
            project_id=project_id,
            participants=participants,
            radius=radius,
            edge_type_whitelist=edge_type_whitelist,
            top_k=top_k,
            max_chapter_id=max_chapter_id,
        )

    def ingest_relations_from_llm(self, project_id: int, data: RelationExtraction, *, volume_number: Optional[int] = None, chapter_number: Optional[int] = None, participants_with_type: Optional[List[ParticipantTyped]] = None) -> Dict[str, Any]:
        # å†™å…¥å…³ç³»ä¸‰å…ƒç»„ï¼›åŒæ—¶æœ€å°æŒä¹…åŒ–ç§°å‘¼/äº‹ä»¶æ‘˜è¦/ç«‹åœºï¼ˆä½œä¸ºå¯æ£€ç´¢è¯æ®ï¼‰
        # tuples: (ä¸»ä½“, å…³ç³», å®¢ä½“, å±žæ€§å­—å…¸)
        triples_with_attrs: List[tuple[str, str, str, Dict[str, Any]]] = []

        DIALOGUES_QUEUE_SIZE = 2
        EVENTS_QUEUE_SIZE = 10

        # åˆ›å»ºå‚ä¸Žè€…ç±»åž‹æ˜ å°„ä»¥ä¾¿å¿«é€ŸæŸ¥æ‰¾
        participant_type_map = {p.name: p.type for p in participants_with_type} if participants_with_type else {}

        def _merge_queue(existing: List[Any], incoming: List[Any], key_fn=lambda x: x, max_size: int = 3) -> List[Any]:
            seen = set()
            merged: List[Any] = []
            # å…ˆæ—§åŽæ–°ï¼Œä¿æŒâ€œæ–°åœ¨é˜Ÿå°¾â€ï¼Œä¹‹åŽè£å‰ªä¿ç•™é˜Ÿå°¾ï¼ˆæœ€è¿‘ï¼‰
            for it in (existing or []) + (incoming or []):
                k = key_fn(it)
                if k in seen:
                    continue
                seen.add(k)
                merged.append(it)
            if len(merged) <= max_size:
                return merged
            return merged[-max_size:]

        # æŒ‰é˜Ÿåˆ—ç­–ç•¥åˆå¹¶å¯¹è¯/äº‹ä»¶æ‘˜è¦ï¼ˆsize=3ï¼‰ï¼Œå¹¶åºåˆ—åŒ–ä¸ºå­—å…¸
        merged_evidence_map: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

        # é¢„å–ï¼šå°†æœ¬æ‰¹æ‰€æœ‰ (a, b, kind_cn) æ”¶é›†ï¼Œåšä¸€æ¬¡å­å›¾æŸ¥è¯¢åŽåœ¨å†…å­˜ä¸­è¿‡æ»¤ï¼Œé¿å…å¤šæ¬¡å¾€è¿”
        pairs: List[Tuple[str, str, str]] = []  # (a, b, kind_en)
        for r in (data.relations or []):
            pred = CN_TO_EN_KIND.get(r.kind or '', '')
            if pred:
                pairs.append((r.a, r.b, pred))

        # æž„å»ºçŽ°å­˜æ•°æ®ç´¢å¼•ï¼škey=(a,b,kind_en) -> {recent_dialogues, recent_event_summaries}
        existing_index: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        try:
            # å‚ä¸Žè€…å…¨é›†ï¼ˆåŽ»é‡ï¼‰
            all_parts = list({p for t in pairs for p in (t[0], t[1])})
            if all_parts:
                sub = self.graph.query_subgraph(project_id=project_id, participants=all_parts, top_k=200)
                from app.schemas.relation_extract import EN_TO_CN_KIND
                for item in (sub.get("relation_summaries") or []):
                    try:
                        a0 = item.get("a"); b0 = item.get("b"); kind_cn = item.get("kind")
                        kind_en = CN_TO_EN_KIND.get(kind_cn or '', '')
                        if not (a0 and b0 and kind_en):
                            continue
                        key = (a0, b0, kind_en)
                        existing_index[key] = {
                            "recent_dialogues": item.get("recent_dialogues") or [],
                            "recent_event_summaries": item.get("recent_event_summaries") or [],
                        }
                    except Exception:
                        continue
        except Exception:
            existing_index = {}

        def _coerce_kind_by_types(kind_cn: str, type_a: Optional[str], type_b: Optional[str]) -> str:
            if not type_a or not type_b:
                return kind_cn
            allowed = _ALLOWED_PAIRS.get(kind_cn)
            if not allowed:
                return kind_cn
            if (type_a, type_b) in allowed:
                return kind_cn
            # ä¸åˆæ³•ï¼šé™çº§ä¸ºâ€œå…³äºŽâ€
            return 'å…³äºŽ'

        for r in (data.relations or []):
            pred = CN_TO_EN_KIND.get(r.kind or '', '')
            if not pred:
                continue
            
            # ä½¿ç”¨ä¼ å…¥çš„ç±»åž‹ä¿¡æ¯ï¼Œå¦‚æžœç¼ºå¤±åˆ™å›žé€€åˆ°çŒœæµ‹
            type_a = participant_type_map.get(r.a) or _guess_entity_type(self.session, project_id, r.a)
            type_b = participant_type_map.get(r.b) or _guess_entity_type(self.session, project_id, r.b)

            # çº¦æŸï¼šä¾æ®å®žä½“ç±»åž‹çŸ«æ­£å…³ç³» kindï¼ˆä¸­æ–‡ï¼‰
            kind_cn_fixed = _coerce_kind_by_types(r.kind, type_a, type_b)
            pred = CN_TO_EN_KIND.get(kind_cn_fixed, pred)
            
            # å‡†å¤‡å±žæ€§å­—å…¸
            attributes = r.model_dump(exclude={"a", "b", "kind"}, exclude_none=True)

            # åŽç«¯å¼ºåˆ¶è¿‡æ»¤ï¼šå¦‚æžœ A æˆ– B ä¸æ˜¯ characterï¼Œåˆ™ç§»é™¤ç§°å‘¼å’Œå¯¹è¯
            if type_a != 'character' or type_b != 'character':
                attributes.pop('a_to_b_addressing', None)
                attributes.pop('b_to_a_addressing', None)
                attributes.pop('recent_dialogues', None)

            # å¯¹è¯ï¼ˆè¿‡æ»¤é•¿åº¦ï¼‰
            new_dialogues = [d.strip() for d in (attributes.get("recent_dialogues") or []) if isinstance(d, str) and len(d.strip()) >= 20]
            if new_dialogues:
                attributes["recent_dialogues"] = new_dialogues
            elif "recent_dialogues" in attributes:
                attributes.pop("recent_dialogues")


            # äº‹ä»¶æ‘˜è¦ï¼ˆè¡¥å…¨å·ç« ï¼‰
            new_summaries: List[Dict[str, Any]] = []
            old_summaries_by_summary: Dict[str, Dict[str, Any]] = {}
            key = (r.a, r.b, pred)
            prev = existing_index.get(key, {})
            old_summaries: List[Dict[str, Any]] = list(prev.get("recent_event_summaries") or [])
            for old_item in old_summaries:
                summary_key = str(old_item.get("summary") or "").strip()
                if summary_key and summary_key not in old_summaries_by_summary:
                    old_summaries_by_summary[summary_key] = old_item

            for s in (r.recent_event_summaries or []):
                try:
                    item = s.model_dump()
                    summary_text = str(item.get("summary") or "").strip()
                    if not summary_text:
                        continue

                    matched_old = old_summaries_by_summary.get(summary_text)
                    if matched_old:
                        if item.get("volume_number") is None and matched_old.get("volume_number") is not None:
                            item["volume_number"] = matched_old.get("volume_number")
                        if item.get("chapter_number") is None and matched_old.get("chapter_number") is not None:
                            item["chapter_number"] = matched_old.get("chapter_number")

                    if volume_number is not None and item.get("volume_number") is None:
                        item["volume_number"] = int(volume_number)
                    if chapter_number is not None and item.get("chapter_number") is None:
                        item["chapter_number"] = int(chapter_number)

                    if summary_text:
                        new_summaries.append(item)
                except Exception:
                    continue

            # è¯»å–çŽ°å­˜å¹¶åˆå¹¶ä¸ºé˜Ÿåˆ—
            old_dialogues: List[str] = list(prev.get("recent_dialogues") or [])

            merged_dialogues = _merge_queue(old_dialogues, new_dialogues, key_fn=lambda x: x, max_size=DIALOGUES_QUEUE_SIZE)
            merged_summaries = _merge_queue(
                old_summaries,
                new_summaries,
                key_fn=lambda x: (
                    str((x or {}).get("summary") or "").strip(),
                    (x or {}).get("volume_number"),
                    (x or {}).get("chapter_number"),
                ),
                max_size=EVENTS_QUEUE_SIZE,
            )

            if merged_dialogues:
                attributes["recent_dialogues"] = merged_dialogues
            if merged_summaries:
                attributes["recent_event_summaries"] = merged_summaries

            # æ¸…ç†ç©ºå­—æ®µ
            if not attributes.get("recent_dialogues") and "recent_dialogues" in attributes:
                attributes.pop("recent_dialogues", None)
            if not attributes.get("recent_event_summaries") and "recent_event_summaries" in attributes:
                attributes.pop("recent_event_summaries", None)
            
            triples_with_attrs.append((r.a, pred, r.b, attributes))
            
            # è¿”å›žå€¼ï¼ˆä»…æ‘˜è¦ï¼‰
            merged_evidence_map[key] = {
                "recent_dialogues": attributes.get("recent_dialogues", []),
                "recent_event_summaries": [s.get('summary') for s in attributes.get("recent_event_summaries", [])]
            }

        if triples_with_attrs:
            try:
                self.graph.ingest_triples_with_attributes(project_id, triples_with_attrs)
            except Exception as e:
                raise ValueError(f"çŸ¥è¯†å›¾è°±å†™å…¥å¤±è´¥: {e}")
        
        return {"written": len(triples_with_attrs), "merged_evidence": merged_evidence_map} 

    def update_dynamic_character_info(self, project_id: int, data: UpdateDynamicInfo, queue_size: int = 3) -> Dict[str, Any]:
        """
        æ›´æ–°è§’è‰²å¡çš„åŠ¨æ€ä¿¡æ¯ï¼Œæ”¯æŒæ–°å¢žã€åˆ é™¤ã€‚
        æ¯ä¸ªç±»åˆ«çš„æœ€å¤§æ•°é‡ä½¿ç”¨ DYNAMIC_INFO_LIMITS ä¸­çš„é…ç½®ï¼›è‹¥æœªé…ç½®ï¼Œåˆ™å›žé€€åˆ° queue_sizeï¼ˆé»˜è®¤3ï¼‰ã€‚
        """
        from app.schemas.entity import CharacterCard

        # 1. å…ˆå¤„ç†åˆ é™¤
        if data.delete_info_list:
            for del_item in data.delete_info_list:
                # å¿ƒç†æƒ³æ³•/ç›®æ ‡å¿«ç…§ï¼šå¿½ç•¥æ¥è‡ª LLM çš„åˆ é™¤æŒ‡ä»¤ï¼Œäº¤ç”±ç³»ç»ŸæŒ‰ FIFO å¤„ç†
                if str(del_item.dynamic_type) == 'å¿ƒç†æƒ³æ³•/ç›®æ ‡å¿«ç…§':
                    continue
                st = select(Card).where(Card.project_id == project_id, Card.title == del_item.name)
                card = self.session.exec(st).first()
                if not card or _card_type_key(card.card_type) != 'character_card':
                    continue
                
                try:
                    model = CharacterCard.model_validate(card.content or {})
                    if model.dynamic_info and del_item.dynamic_type in model.dynamic_info:
                        model.dynamic_info[del_item.dynamic_type] = [
                            item for item in model.dynamic_info[del_item.dynamic_type] if item.id != del_item.id
                        ]
                        card.content = model.model_dump(exclude_unset=True)
                        flag_modified(card, "content")
                        self.session.add(card)
                except Exception as e:
                    logger.warning(f"Failed to process deletion for {del_item.name}: {e}")
            self.session.commit()

        # 2. å†å¤„ç†æ–°å¢žä¸Žä¿®æ”¹
        updated_cards: Dict[str, Card] = {}
        # é¢„åŠ è½½æ‰€æœ‰ç›¸å…³çš„è§’è‰²å¡
        all_names = list(set([i.name for i in data.info_list]))
        if not all_names:
            return {"success": False, "updated_card_count": 0}

        stmt = select(Card).where(Card.project_id == project_id, Card.title.in_(all_names))
        cards = self.session.exec(stmt).all()
        card_map = {c.title: c for c in cards if c.card_type and _card_type_key(c.card_type) == 'character_card'}


        # å¤„ç†æ–°å¢ž
        # (å’Œä¹‹å‰ç±»ä¼¼ï¼Œä½†è¦ç¡®ä¿åœ¨å·²æ›´æ–°çš„ card å¯¹è±¡ä¸Šæ“ä½œ)
        for info_group in data.info_list:
            card = updated_cards.get(info_group.name) or card_map.get(info_group.name)
            if not card:
                continue

            try:
                model = CharacterCard.model_validate(card.content or {})
                if not model.dynamic_info:
                    model.dynamic_info = {}

                for cat, items in info_group.dynamic_info.items():
                    if not items:
                        continue
                    
                    if cat not in model.dynamic_info:
                        model.dynamic_info[cat] = []
                    
                    existing_items = model.dynamic_info[cat]
                    
                    # åˆå¹¶ï¼ˆæ–°é¡¹è¿½åŠ åœ¨é˜Ÿå°¾ï¼Œä¾¿äºŽ FIFOï¼‰
                    for new_item in items:
                        # å°†å ä½æˆ–ç¼ºå¤±IDæš‚è®°ä¸º 0ï¼Œç¨åŽç»Ÿä¸€åˆ†é…æ­£æ•°ID
                        if not isinstance(new_item.id, int) or new_item.id <= 0:
                            new_item.id = 0
                        existing_items.append(new_item)
                    
                    # ç»Ÿä¸€IDè§„èŒƒåŒ–ï¼šä¸ºæ‰€æœ‰ <=0 çš„æ¡ç›®åˆ†é…è¿žç»­æ­£æ•°IDï¼ˆä¸æ”¹å˜å·²æœ‰æ­£æ•°IDï¼‰
                    existing_positive = [it.id for it in existing_items if isinstance(it.id, int) and it.id > 0]
                    next_id = (max(existing_positive) + 1) if existing_positive else 1
                    for it in existing_items:
                        if not isinstance(it.id, int) or it.id <= 0:
                            it.id = next_id
                            next_id += 1
                    
                    # æŒ‰é…ç½®ä¸Šé™è£å‰ª
                    limit = DYNAMIC_INFO_LIMITS.get(cat, queue_size)
                    if str(cat) == 'å¿ƒç†æƒ³æ³•/ç›®æ ‡å¿«ç…§':
                        # ä¿ç•™æœ€æ–° limit æ¡ï¼ˆå…ˆè¿›å…ˆå‡ºï¼Œæ·˜æ±°æœ€æ—§ï¼‰
                        model.dynamic_info[cat] = existing_items[-limit:]
                    else:
                        # å…¶ä»–ç±»åˆ«æ²¿ç”¨å½“å‰ç­–ç•¥ï¼ˆè‹¥éœ€æ”¹ä¸ºä¿ç•™æœ€æ–°ï¼Œå¯æ”¹ä¸º existing_items[-limit:]ï¼‰
                        model.dynamic_info[cat] = existing_items[:limit]

                card.content = model.model_dump(exclude_unset=True)
                flag_modified(card, "content")
                updated_cards[card.title] = card
            except Exception as e:
                logger.warning(f"Failed to process addition for {info_group.name}: {e}")

        # ç»Ÿä¸€æäº¤
        for card in updated_cards.values():
            self.session.add(card)
        
        if updated_cards:
            self.session.commit()
            for card in updated_cards.values():
                self.session.refresh(card)

        return {"success": True, "updated_card_count": len(updated_cards)}
