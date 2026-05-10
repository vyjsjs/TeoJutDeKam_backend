from sqlalchemy import Column, BigInteger, String, Integer, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # nullable for social login
    nickname = Column(String(100), nullable=False)
    profile_image_url = Column(String(500), nullable=True)
    login_type = Column(String(50), nullable=False, default="local")  # local, kakao, google
    provider_id = Column(String(255), nullable=True)  # social provider user id
    total_points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    visit_certifications = relationship("VisitCertification", back_populates="user", lazy="selectin")
    reviews = relationship("Review", back_populates="user", lazy="selectin")
    store_user_stats = relationship("StoreUserStats", back_populates="user", lazy="selectin")
    point_histories = relationship("PointHistory", back_populates="user", lazy="selectin")
