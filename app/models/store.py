from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    address = Column(String(500), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    phone = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    visit_certifications = relationship("VisitCertification", back_populates="store", lazy="selectin")
    reviews = relationship("Review", back_populates="store", lazy="selectin")
    store_user_stats = relationship("StoreUserStats", back_populates="store", lazy="selectin")
    point_histories = relationship("PointHistory", back_populates="store", lazy="selectin")
