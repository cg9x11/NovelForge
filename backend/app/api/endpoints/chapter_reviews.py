from app.locales import localized_text
from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.chapter_review import (
    ReviewCardUpsertRequest,
    ReviewResultCardRead,
    ReviewRunRequest,
    ReviewRunResponse,
)
from app.schemas.response import ApiResponse
from app.services.review.review_service import (
    delete_review_result_card,
    list_reviews_by_card,
    run_review,
    upsert_review_result_card,
)


router = APIRouter()


@router.post(
    "/cards/run",
    response_model=ApiResponse[ReviewRunResponse],
    summary=localized_text('hardcoded.api_endpoints_chapter_reviews_772747e8'),
)
async def run_review_endpoint(
    request: ReviewRunRequest,
    session: Session = Depends(get_session),
):
    result = await run_review(session, request)
    return ApiResponse(data=result)


@router.post(
    "/cards/upsert",
    response_model=ApiResponse[ReviewResultCardRead],
    summary=localized_text('hardcoded.api_endpoints_chapter_reviews_bd3c0aa5'),
)
def upsert_review_card_endpoint(
    request: ReviewCardUpsertRequest,
    session: Session = Depends(get_session),
):
    card = upsert_review_result_card(session, request)
    return ApiResponse(data=card)


@router.get(
    "/cards/{card_id}",
    response_model=ApiResponse[List[ReviewResultCardRead]],
    summary=localized_text('hardcoded.api_endpoints_chapter_reviews_81383bd1'),
)
def list_review_cards_by_target_endpoint(
    card_id: int,
    session: Session = Depends(get_session),
):
    return ApiResponse(data=list_reviews_by_card(session, card_id))


@router.delete(
    "/{review_card_id}",
    response_model=ApiResponse[bool],
    summary=localized_text('hardcoded.api_endpoints_chapter_reviews_35c04e87'),
)
def delete_review_card_endpoint(
    review_card_id: int,
    session: Session = Depends(get_session),
):
    return ApiResponse(data=delete_review_result_card(session, review_card_id))
