from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship('Session', back_populates='user')

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    user = relationship('User', back_populates='sessions')
    chats = relationship('ChatHistory', back_populates='session')

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    llm_response_metadata = Column(JSON)  # Store LLM API details, tokens, etc.
    session = relationship('Session', back_populates='chats')

class WebSearchLog(Base):
    __tablename__ = 'web_search_logs'
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chat_history.id'))
    query = Column(Text, nullable=False)
    search_results = Column(JSON)  # Store raw results from Serper or similar
    timestamp = Column(DateTime, default=datetime.utcnow)
    chat = relationship('ChatHistory')

class LoanSimulation(Base):
    __tablename__ = 'loan_simulations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    eligibility_score = Column(Float)
    simulation_input = Column(JSON)  # Store user input for simulation
    simulation_result = Column(JSON)  # Store result details
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User')

