from sqlalchemy import Column, BigInteger, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class VisitCertification(Base):
    __tablename__ = "visit_certifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id = Column(BigInteger, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    user_latitude = Column(Numeric(10, 7), nullable=False)
    user_longitude = Column(Numeric(10, 7), nullable=False)
    distance_meters = Column(Integer, nullable=True)
    certification_type = Column(String(50), nullable=False)  # gps, receipt
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected
    earned_points = Column(Integer, nullable=False, default=0)
    certified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="visit_certifications")
    store = relationship("Store", back_populates="visit_certifications")
    reviews = relationship(
        "Review",
        back_populates="visit_certification",
        lazy="selectin",
        uselist=False,
    )
    point_histories = relationship("PointHistory", back_populates="visit_certification", lazy="selectin")
