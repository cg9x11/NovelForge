from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.db.session import get_session
from app.schemas.prompt import KnowledgeRead, KnowledgeCreate, KnowledgeUpdate
from app.schemas.response import ApiResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter()

@router.get('/', response_model=ApiResponse[List[KnowledgeRead]], summary='获取知识库列表')
def list_knowledge(session: Session = Depends(get_session)):
    svc = KnowledgeService(session)
    items = svc.list()
    return ApiResponse(data=items)

@router.post('/', response_model=ApiResponse[KnowledgeRead], summary='创建知识库')
def create_knowledge(body: KnowledgeCreate, session: Session = Depends(get_session)):
    svc = KnowledgeService(session)
    if svc.get_by_name(body.name):
        raise HTTPException(status_code=400, detail='Knowledge with same name already exists')
    if body.key and svc.get_by_key(body.key):
        raise HTTPException(status_code=400, detail='Knowledge with same key already exists')
    item = svc.create(key=body.key, name=body.name, description=body.description, content=body.content)
    return ApiResponse(data=item)

@router.get('/{kid}', response_model=ApiResponse[KnowledgeRead], summary='获取单个知识库')
def get_knowledge(kid: int, session: Session = Depends(get_session)):
    svc = KnowledgeService(session)
    item = svc.get_by_id(kid)
    if not item:
        raise HTTPException(status_code=404, detail='Knowledge not found')
    return ApiResponse(data=item)

@router.put('/{kid}', response_model=ApiResponse[KnowledgeRead], summary='更新知识库')
def update_knowledge(kid: int, body: KnowledgeUpdate, session: Session = Depends(get_session)):
    svc = KnowledgeService(session)
    if body.key:
        existing = svc.get_by_key(body.key)
        if existing and existing.id != kid:
            raise HTTPException(status_code=400, detail='Duplicate knowledge key')
    item = svc.update(kid, key=body.key, name=body.name, description=body.description, content=body.content)
    if not item:
        raise HTTPException(status_code=404, detail='Knowledge not found')
    return ApiResponse(data=item)

@router.delete('/{kid}', response_model=ApiResponse, summary='删除知识库')
def delete_knowledge(kid: int, session: Session = Depends(get_session)):
    svc = KnowledgeService(session)
    item = svc.get_by_id(kid)
    if not item:
        raise HTTPException(status_code=404, detail='Knowledge not found')
    if getattr(item, 'built_in', False):
        raise HTTPException(status_code=400, detail='Built-in knowledge cannot be deleted')
    ok = svc.delete(kid)
    if not ok:
        raise HTTPException(status_code=404, detail='Knowledge not found')
    return ApiResponse(message='Deleted successfully')
