"""
çµæ„ŸåŠ©æ‰‹ä¸“ç”¨æŽ¥å£
æ”¯æŒå·¥å…·è°ƒç”¨çš„å¯¹è¯
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator
from loguru import logger

from app.db.session import get_session
from app.services.ai.assistant.assistant_service import generate_assistant_chat_streaming
from app.schemas.ai import AssistantChatRequest
from app.utils.stream_utils import wrap_sse_stream

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat")
async def assistant_chat(
    request: AssistantChatRequest,
    session: Session = Depends(get_session)
):
    """
    çµæ„ŸåŠ©æ‰‹å¯¹è¯æŽ¥å£ï¼ˆæ”¯æŒå·¥å…·è°ƒç”¨ï¼‰
    
    ç‰¹ç‚¹ï¼š
    - ä¸“ç”¨è¯·æ±‚æ¨¡åž‹ï¼ˆè¯­ä¹‰æ¸…æ™°ï¼‰
    - è‡ªåŠ¨æ³¨å…¥å·¥å…·é›†
    - æ”¯æŒæµå¼è¾“å‡º
    - æ”¯æŒå·¥å…·è°ƒç”¨ç»“æžœè¿”å›ž
    """
    # åŠ è½½ç³»ç»Ÿæç¤ºè¯ï¼ˆæ ¹æ®æ¨¡å¼é€‰æ‹©ä¸åŒçš„æç¤ºè¯ï¼‰
    from app.services import prompt_service
    
    prompt_name = request.prompt_name
    react_enabled = bool(getattr(request, "react_mode_enabled", False))

    if react_enabled:
        react_prompt_name = f"{prompt_name}-React"
        p = prompt_service.get_prompt_by_identifier(session, react_prompt_name)
        if p and p.template:
            system_prompt = str(p.template)
            logger.info(f"[Assistant API] React æ¨¡å¼å¯ç”¨ï¼Œä½¿ç”¨æç¤ºè¯ {react_prompt_name}")
        else:
            logger.warning(f"[Assistant API] React æ¨¡å¼å¯ç”¨ä½†æœªæ‰¾åˆ° {react_prompt_name}ï¼Œé€€å›žæ ‡å‡†æç¤ºè¯ {prompt_name}")
            p = prompt_service.get_prompt_by_identifier(session, prompt_name)
            if not p or not p.template:
                raise HTTPException(status_code=400, detail={"error_code": "PROMPT_NOT_FOUND", "prompt_name": prompt_name})
            system_prompt = str(p.template)
    else:
        p = prompt_service.get_prompt_by_identifier(session, prompt_name)
        if not p or not p.template:
            raise HTTPException(status_code=400, detail={"error_code": "PROMPT_NOT_FOUND", "prompt_name": prompt_name})
        system_prompt = str(p.template)
    
    # æ‰€æœ‰æ¨¡å¼ç»Ÿä¸€èµ° LangChain ChatModel + Tools ç®¡çº¿
    async def stream_with_tools() -> AsyncGenerator[str, None]:
        logger.info("[Assistant API] ä½¿ç”¨{}æ¨¡å¼".format("React" if react_enabled else "æ ‡å‡†"))
        async for chunk in generate_assistant_chat_streaming(
            session=session,
            request=request,
            system_prompt=system_prompt,
            track_stats=True,
        ):
            yield chunk
    
    return StreamingResponse(
        wrap_sse_stream(stream_with_tools()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

