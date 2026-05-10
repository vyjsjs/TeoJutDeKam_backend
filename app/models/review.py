from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(BigInteger, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    visit_certification_id = Column(BigInteger, ForeignKey("visit_certifications.id", ondelete="SET NULL"), nullable=True)
    rating = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    earned_points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="reviews")
    store = relationship("Store", back_populates="reviews")
    visit_certification = relationship("VisitCertification", back_populates="reviews")
    point_histories = relationship("PointHistory", back_populates="review", lazy="selectin")
