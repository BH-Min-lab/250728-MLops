# [file] interface / recommendation_router.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from infra.db.db import get_db
from application.services.recommendation_service import get_recommendation_products_with_user
from application.schemas.recommendation import RecommendationResponse  

router = APIRouter()

@router.get("/recommendations/home", response_model=RecommendationResponse)
def homepage_recommendation(
    user_id: int = Query(..., description="유저 ID"),
    db: Session = Depends(get_db)
):
    return get_recommendation_products_with_user(db, user_id)