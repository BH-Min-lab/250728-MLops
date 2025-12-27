# [file] infra/db_models/recommendation.py
# [description] DB recommendation (1) 추천 결과
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from infra.db.db import Base
from infra.enums.model_type import ModelType   

import enum

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recommended_items = Column(Text, nullable=False)
    model_type = Column(
        SqlEnum(ModelType, name="model_type_enum"),
        nullable=False,
        default=ModelType.DEEP_LEARNING
    )
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")