from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PointHistory(Base):
    __tablename__ = "point_histories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(BigInteger, ForeignKey("stores.id", ondelete="CASCADE"), nullable=True)
    visit_certification_id = Column(BigInteger, ForeignKey("visit_certifications.id", ondelete="SET NULL"), nullable=True)
    review_id = Column(BigInteger, ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True)
    point_type = Column(String(50), nullable=False)  # visit, review, bonus
    point_amount = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="point_histories")
    store = relationship("Store", back_populates="point_histories")
    visit_certification = relationship("VisitCertification", back_populates="point_histories")
    review = relationship("Review", back_populates="point_histories")
