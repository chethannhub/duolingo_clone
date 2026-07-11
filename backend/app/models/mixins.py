from sqlalchemy import Column, Text, text as sql_text


class TimestampMixin:
    created_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
    updated_at = Column(Text, nullable=False, server_default=sql_text("CURRENT_TIMESTAMP"))
