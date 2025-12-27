from pydantic import BaseModel
from typing import List, Optional

class RecommendationItem(BaseModel):
    category_id: int
    product_id: int
    title: str
    price: float
    image_url: Optional[str]

class RecommendationResponse(BaseModel):
    user_nickname: Optional[str]
    recommendations: List[RecommendationItem]