from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

# Declarative base for ORM
Base = declarative_base()

class Intent(Base):
    __tablename__ = 'intents'

    id = Column(Integer, primary_key=True, index=True)

     
    # Add these lines ⬇️
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    loan_type = Column(String, nullable=True)
    last_user_query = Column(Text, nullable=True)

    # 🔑 Identifiers for user and session tracking
    user_uuid = Column(UUID(as_uuid=True), index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)

    # 💬 Conversation log
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=True)

    # 🧠 NLP-detected intent
    intent = Column(String, nullable=True)  # e.g., "loan_inquiry", "greeting", etc.

    # # 🏷️ Optional metadata for future use or personalization
    # name = Column(String, index=True, nullable=True)       # e.g., user name
    # description = Column(String, nullable=True)            # e.g., context description

    # 📦 Structured payloads
    parameters = Column(JSON, nullable=True)  # location, income, timeline, etc.
    context = Column(JSON, nullable=True)     # chatbot state or summary

    # 🕒 Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
