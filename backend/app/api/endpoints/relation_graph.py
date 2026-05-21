from __future__ import annotations
from app.locales import localized_text

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.relation_graph import (
    RelationGraphBatchAppendEventsRequest,
    RelationGraphBatchCreateRequest,
    RelationGraphBatchDeleteRequest,
    RelationGraphBatchUpdateKindRequest,
    RelationGraphBatchUpdateStanceRequest,
    RelationGraphDeleteRequest,
    RelationGraphExportRequest,
    RelationGraphExportResponse,
    RelationGraphImportRequest,
    RelationGraphImportResponse,
    RelationGraphListRequest,
    RelationGraphListResponse,
    RelationGraphMetaResponse,
    RelationGraphRecord,
    RelationGraphUpsertRequest,
    RelationGraphWriteResponse,
)
from app.services.relation_graph_service import RelationGraphService


router = APIRouter()


def _service(session: Session) -> RelationGraphService:
    return RelationGraphService(session)


@router.get("/meta", response_model=RelationGraphMetaResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_15d087df'))
def get_meta(session: Session = Depends(get_session)):
    return _service(session).get_meta()


@router.post("/list", response_model=RelationGraphListResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_69f376c1'))
def list_relations(req: RelationGraphListRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).list_relations(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upsert", response_model=RelationGraphRecord, summary=localized_text('hardcoded.api_endpoints_relation_graph_b6246537'))
def upsert_relation(req: RelationGraphUpsertRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).upsert_relation(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete", response_model=RelationGraphWriteResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_2de42b5b'))
def delete_relation(req: RelationGraphDeleteRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).delete_relation(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/delete", response_model=RelationGraphWriteResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_1946d0e7'))
def batch_delete(req: RelationGraphBatchDeleteRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).batch_delete_relations(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/update-kind", response_model=RelationGraphWriteResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_910f997e'))
def batch_update_kind(req: RelationGraphBatchUpdateKindRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).batch_update_kind(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/update-stance", response_model=RelationGraphWriteResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_71c2cf34'))
def batch_update_stance(req: RelationGraphBatchUpdateStanceRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).batch_update_stance(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/append-events", response_model=RelationGraphWriteResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_e9248b4a'))
def batch_append_events(req: RelationGraphBatchAppendEventsRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).batch_append_events(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/create", response_model=RelationGraphWriteResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_5396b729'))
def batch_create(req: RelationGraphBatchCreateRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).batch_create_relations(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export", response_model=RelationGraphExportResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_3ef9e03d'))
def export_relations(req: RelationGraphExportRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).export_relations(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import", response_model=RelationGraphImportResponse, summary=localized_text('hardcoded.api_endpoints_relation_graph_5324d5d1'))
def import_relations(req: RelationGraphImportRequest, session: Session = Depends(get_session)):
    try:
        return _service(session).import_relations(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
