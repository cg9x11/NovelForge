from app.locales import localized_text
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.prompt import PromptRead, PromptCreate, PromptUpdate
from app.schemas.response import ApiResponse
from app.services import prompt_service

router = APIRouter()

@router.post("/", response_model=ApiResponse[PromptRead], summary=localized_text('hardcoded.api_endpoints_prompts_bbaaa09b'))
def create_prompt(
    *,
    session: Session = Depends(get_session),
    prompt: PromptCreate,
):
    try:
        new_prompt = prompt_service.create_prompt(session=session, prompt_create=prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=new_prompt)

@router.get("/", response_model=ApiResponse[List[PromptRead]], summary=localized_text('hardcoded.api_endpoints_prompts_e32cd150'))
def read_prompts(
    *,
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
):
    prompts = prompt_service.get_prompts(session=session, skip=skip, limit=limit)
    return ApiResponse(data=prompts)

@router.get("/{prompt_id}", response_model=ApiResponse[PromptRead], summary=localized_text('hardcoded.api_endpoints_prompts_fa981b9a'))
def read_prompt(
    *,
    session: Session = Depends(get_session),
    prompt_id: int,
):
    db_prompt = prompt_service.get_prompt(session=session, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return ApiResponse(data=db_prompt)

@router.put("/{prompt_id}", response_model=ApiResponse[PromptRead], summary=localized_text('hardcoded.api_endpoints_prompts_9a80c960'))
def update_prompt(
    *,
    session: Session = Depends(get_session),
    prompt_id: int,
    prompt: PromptUpdate,
):
    try:
        updated_prompt = prompt_service.update_prompt(session=session, prompt_id=prompt_id, prompt_update=prompt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return ApiResponse(data=updated_prompt)

@router.delete("/{prompt_id}", response_model=ApiResponse, summary=localized_text('hardcoded.api_endpoints_prompts_9ce1dbb9'))
def delete_prompt(
    *,
    session: Session = Depends(get_session),
    prompt_id: int,
):
    db_prompt = prompt_service.get_prompt(session=session, prompt_id=prompt_id)
    if not db_prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    if getattr(db_prompt, 'built_in', False):
        raise HTTPException(status_code=400, detail="Built-in prompt cannot be deleted")
    if not prompt_service.delete_prompt(session=session, prompt_id=prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return ApiResponse(message="Prompt deleted successfully")
