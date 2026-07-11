from sqlalchemy import CheckConstraint, Column, Index, Integer, Text, UniqueConstraint, text as sql_text

from app.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("learner_id", "scope", "idempotency_key"),
        Index("ix_idempotency_records_lookup", "learner_id", "scope", "idempotency_key"),
        CheckConstraint("status_code BETWEEN 100 AND 599", name="ck_idempotency_status_code"),
    )

    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, nullable=False)
    scope = Column(Text, nullable=False)
    idempotency_key = Column(Text, nullable=False)
    request_hash = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=False, server_default="200")
    response_json = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
