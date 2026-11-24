import json
from datetime import datetime
from sqlalchemy import Column, Integer, Text, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class BiometricProfile(Base):
    __tablename__ = "biometric_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    # Store list of embeddings as JSON string: [[...], [...]]
    embeddings_json = Column(Text, nullable=False)
    sample_count = Column(Integer, default=1)
    quality_score = Column(Float, default=1.0)
    encoding_version = Column(String(30), default="sface_v1")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="biometric_profile")

    def get_embeddings(self) -> list:
        try:
            return json.loads(self.embeddings_json)
        except Exception:
            return []

    def set_embeddings(self, embeddings_list: list):
        self.embeddings_json = json.dumps(embeddings_list)
