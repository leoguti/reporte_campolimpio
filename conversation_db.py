"""
Módulo de base de datos para persistencia de conversaciones.
Usa SQLite para almacenar el estado de las conversaciones con el agente.

Para inicializar la base de datos, ejecutar:
    python -c "from conversation_db import init_db; init_db()"

O simplemente ejecutar el servidor - se creará automáticamente si no existe.
"""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from conversation_state import ConversationState

# Configuración de SQLAlchemy
DATABASE_URL = "sqlite:///./conversations.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Conversation(Base):
    """Modelo de tabla para almacenar conversaciones"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    conversation_id = Column(String, index=True, nullable=False, unique=True)
    state_json = Column(Text, nullable=False)  # JSON serializado del ConversationState
    status = Column(String, nullable=False)  # Para queries rápidas sin deserializar
    started_at = Column(DateTime, nullable=False)
    last_update_at = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<Conversation {self.conversation_id} - {self.status}>"


def init_db():
    """Crea todas las tablas en la base de datos"""
    Base.metadata.create_all(bind=engine)
    print("✓ Base de datos inicializada")


def get_db() -> Session:
    """Obtiene una sesión de base de datos"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Se cierra manualmente donde se use


def find_conversation(user_id: str, conversation_id: str) -> Optional[ConversationState]:
    """
    Busca una conversación activa por user_id y conversation_id.
    
    Returns:
        ConversationState si existe, None si no se encuentra
    """
    db = get_db()
    try:
        conv = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.conversation_id == conversation_id
        ).first()
        
        if conv:
            # Deserializar JSON a ConversationState
            state_dict = json.loads(conv.state_json)
            return ConversationState.from_dict(state_dict)
        
        return None
    finally:
        db.close()


def find_latest_conversation(user_id: str) -> Optional[ConversationState]:
    """
    Busca la conversación más reciente de un usuario.
    
    Returns:
        ConversationState si existe, None si no hay conversaciones
    """
    db = get_db()
    try:
        conv = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.last_update_at.desc()).first()
        
        if conv:
            state_dict = json.loads(conv.state_json)
            return ConversationState.from_dict(state_dict)
        
        return None
    finally:
        db.close()


def create_conversation(state: ConversationState) -> Conversation:
    """
    Crea una nueva conversación en la base de datos.
    
    Args:
        state: ConversationState a persistir
        
    Returns:
        Objeto Conversation creado
    """
    db = get_db()
    try:
        state_dict = state.to_dict()
        
        conv = Conversation(
            user_id=state.meta["user_id"],
            conversation_id=state.meta["conversation_id"],
            state_json=json.dumps(state_dict, ensure_ascii=False),
            status=state.conversation["status"],
            started_at=datetime.fromisoformat(state.meta["started_at"]),
            last_update_at=datetime.fromisoformat(state.meta["last_update_at"])
        )
        
        db.add(conv)
        db.commit()
        db.refresh(conv)
        
        return conv
    finally:
        db.close()


def update_conversation(state: ConversationState) -> Conversation:
    """
    Actualiza una conversación existente en la base de datos.
    Si no existe, la crea.
    
    Args:
        state: ConversationState actualizado
        
    Returns:
        Objeto Conversation actualizado
    """
    db = get_db()
    try:
        conv = db.query(Conversation).filter(
            Conversation.conversation_id == state.meta["conversation_id"]
        ).first()
        
        if not conv:
            # Si no existe, crearla
            db.close()
            return create_conversation(state)
        
        # Actualizar campos
        state_dict = state.to_dict()
        conv.state_json = json.dumps(state_dict, ensure_ascii=False)
        conv.status = state.conversation["status"]
        conv.last_update_at = datetime.fromisoformat(state.meta["last_update_at"])
        
        db.commit()
        db.refresh(conv)
        
        return conv
    finally:
        db.close()


def get_or_create_conversation(user_id: str, conversation_id: str = None) -> ConversationState:
    """
    Obtiene una conversación existente o crea una nueva.
    
    Args:
        user_id: ID del usuario
        conversation_id: ID de la conversación (opcional, se genera si no existe)
        
    Returns:
        ConversationState (existente o nuevo)
    """
    if conversation_id:
        # Intentar buscar conversación existente
        state = find_conversation(user_id, conversation_id)
        if state:
            return state
    
    # Crear nueva conversación
    state = ConversationState(user_id, conversation_id)
    create_conversation(state)
    
    return state


def delete_conversation(conversation_id: str) -> bool:
    """
    Elimina una conversación de la base de datos.
    
    Returns:
        True si se eliminó, False si no existía
    """
    db = get_db()
    try:
        conv = db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()
        
        if conv:
            db.delete(conv)
            db.commit()
            return True
        
        return False
    finally:
        db.close()


def list_user_conversations(user_id: str, limit: int = 10):
    """
    Lista las conversaciones recientes de un usuario.
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de conversaciones a retornar
        
    Returns:
        Lista de ConversationState
    """
    db = get_db()
    try:
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.last_update_at.desc()).limit(limit).all()
        
        return [
            ConversationState.from_dict(json.loads(conv.state_json))
            for conv in conversations
        ]
    finally:
        db.close()


# Inicializar la base de datos al importar el módulo
try:
    init_db()
except Exception as e:
    print(f"Advertencia: No se pudo inicializar la BD: {e}")
