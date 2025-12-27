# [file] application / recommendation_service.py
from sqlalchemy.orm import Session, joinedload
from infra.db_models.recommendation import Recommendation
from infra.db_models.product import Product, Category
from infra.db_models.user import User
from application.schemas.recommendation import RecommendationResponse, RecommendationItem

def get_recommendation_products_with_user(db: Session, user_id: int, limit: int = 4) -> RecommendationResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RecommendationResponse(user_nickname=None, recommendations=[])

    user_nickname = user.nickname

    recommendation = db.query(Recommendation)\
        .filter(Recommendation.user_id == user_id)\
        .order_by(Recommendation.generated_at.desc())\
        .first()

    if not recommendation:
        return RecommendationResponse(user_nickname=user_nickname, recommendations=[])

    recommended_texts = [text.strip() for text in recommendation.recommended_items.split(",") if text.strip()]
    if not recommended_texts:
        return RecommendationResponse(user_nickname=user_nickname, recommendations=[])

    first_text = recommended_texts[0]

    matched_category = db.query(Category)\
        .filter(Category.name.ilike(f"%{first_text}%"))\
        .first()
    if not matched_category:
        return RecommendationResponse(user_nickname=user_nickname, recommendations=[])

    category_id = matched_category.id

    recommended_products = db.query(Product)\
        .options(joinedload(Product.images))\
        .filter(Product.category_id == category_id)\
        .order_by(Product.created_at.desc())\
        .limit(limit)\
        .all()

    result = [
        RecommendationItem(
            category_id=category_id,
            product_id=p.id,
            title=p.title,
            price=float(p.price),
            image_url=p.images[0].image_url if p.images else None
        )
        for p in recommended_products
    ]

    return RecommendationResponse(user_nickname=user_nickname, recommendations=result)