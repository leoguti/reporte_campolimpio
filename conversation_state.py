from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ConversationStatus(Enum):
    """Estados posibles de la conversación"""
    BUILDING = "building"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    READY_TO_EXECUTE = "ready_to_execute"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class IssueType(Enum):
    """Tipos de problemas detectados en la consulta"""
    MISSING_FILTER = "missing_filter"
    AMBIGUOUS_TERM = "ambiguous_term"
    INVALID_FIELD = "invalid_field"
    IMPOSSIBLE_REQUEST = "impossible_request"


class ConversationState:
    """
    Maneja el estado completo de una conversación con el agente.
    Encapsula metadata, progreso de conversación, query building, issues y history.
    """
    
    def __init__(self, user_id: str, conversation_id: str = None):
        """Inicializa un nuevo estado de conversación"""
        now = datetime.utcnow().isoformat()
        
        # Metadata
        self.meta = {
            "user_id": user_id,
            "conversation_id": conversation_id or f"{user_id}_{now}",
            "started_at": now,
            "last_update_at": now,
            "language": "es"
        }
        
        # Estado de la conversación
        self.conversation = {
            "status": ConversationStatus.BUILDING.value,
            "step": None,  # tipo_reporte, periodo, region, etc.
            "pending_question": None,
            "last_user_message": None,
            "last_agent_message": None
        }
        
        # Query building (lo que se va construyendo para Airtable)
        self.query = {
            "type": None,  # coordinadores, visitas, materiales, etc.
            "table": None,  # Certificados, Kardex
            "filters": {},  # fecha_desde, fecha_hasta, coordinador, municipio, etc.
            "fields": [],  # campos a retornar
            "sort": [],  # ordenamiento
            "limit": 100,
            "validated": False
        }
        
        # Issues detectados
        self.issues = []  # [{type, field, message}]
        
        # Estado de ejecución
        self.execution = {
            "ready": False,
            "last_run_at": None,
            "result_summary": None,
            "error": None
        }
        
        # History de mensajes (últimos N turnos)
        self.history = []  # [{role: "user"/"agent", content, timestamp}]
    
    def update_status(self, status: ConversationStatus):
        """Actualiza el estado de la conversación"""
        self.conversation["status"] = status.value
        self._update_timestamp()
    
    def update_step(self, step: str):
        """Actualiza el paso actual de la conversación"""
        self.conversation["step"] = step
        self._update_timestamp()
    
    def set_pending_question(self, question: str):
        """Establece una pregunta pendiente del agente al usuario"""
        self.conversation["pending_question"] = question
        self.update_status(ConversationStatus.AWAITING_CLARIFICATION)
    
    def clear_pending_question(self):
        """Limpia la pregunta pendiente"""
        self.conversation["pending_question"] = None
    
    def update_query_type(self, query_type: str, table: str = None):
        """Actualiza el tipo de consulta y opcionalmente la tabla"""
        self.query["type"] = query_type
        if table:
            self.query["table"] = table
        self._update_timestamp()
    
    def add_filter(self, key: str, value: Any):
        """Agrega o actualiza un filtro de la query"""
        self.query["filters"][key] = value
        self._update_timestamp()
    
    def remove_filter(self, key: str):
        """Elimina un filtro"""
        if key in self.query["filters"]:
            del self.query["filters"][key]
            self._update_timestamp()
    
    def set_fields(self, fields: List[str]):
        """Establece los campos a retornar"""
        self.query["fields"] = fields
        self._update_timestamp()
    
    def set_sort(self, sort: List[Dict[str, str]]):
        """Establece el ordenamiento. Ej: [{"field": "fecha", "direction": "desc"}]"""
        self.query["sort"] = sort
        self._update_timestamp()
    
    def set_limit(self, limit: int):
        """Establece el límite de registros"""
        self.query["limit"] = limit
        self._update_timestamp()
    
    def validate_query(self):
        """Marca la query como validada"""
        self.query["validated"] = True
        self.execution["ready"] = True
        self.update_status(ConversationStatus.READY_TO_EXECUTE)
    
    def add_issue(self, issue_type: IssueType, field: str = None, message: str = None):
        """Agrega un problema detectado"""
        issue = {
            "type": issue_type.value,
            "field": field,
            "message": message,
            "detected_at": datetime.utcnow().isoformat()
        }
        self.issues.append(issue)
        self._update_timestamp()
    
    def clear_issues(self):
        """Limpia todos los issues"""
        self.issues = []
        self._update_timestamp()
    
    def add_message(self, role: str, content: str, max_history: int = 10):
        """
        Agrega un mensaje al historial.
        Args:
            role: "user" o "agent"
            content: contenido del mensaje
            max_history: número máximo de mensajes a mantener
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.history.append(message)
        
        # Mantener solo los últimos N mensajes
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
        
        # Actualizar last_user_message o last_agent_message
        if role == "user":
            self.conversation["last_user_message"] = content
        elif role == "agent":
            self.conversation["last_agent_message"] = content
        
        self._update_timestamp()
    
    def mark_executed(self, result_summary: str = None, error: str = None):
        """Marca la consulta como ejecutada"""
        self.execution["last_run_at"] = datetime.utcnow().isoformat()
        self.execution["result_summary"] = result_summary
        self.execution["error"] = error
        
        if error:
            self.update_status(ConversationStatus.CANCELLED)
        else:
            self.update_status(ConversationStatus.EXECUTED)
    
    def reset_for_new_query(self):
        """Reinicia el estado para una nueva consulta manteniendo el contexto"""
        self.conversation["status"] = ConversationStatus.BUILDING.value
        self.conversation["step"] = None
        self.conversation["pending_question"] = None
        
        self.query = {
            "type": None,
            "table": None,
            "filters": {},
            "fields": [],
            "sort": [],
            "limit": 100,
            "validated": False
        }
        
        self.issues = []
        
        self.execution = {
            "ready": False,
            "last_run_at": None,
            "result_summary": None,
            "error": None
        }
        
        self._update_timestamp()
    
    def _update_timestamp(self):
        """Actualiza el timestamp de última modificación"""
        self.meta["last_update_at"] = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el estado a diccionario JSON-compatible"""
        return {
            "meta": self.meta,
            "conversation": self.conversation,
            "query": self.query,
            "issues": self.issues,
            "execution": self.execution,
            "history": self.history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Deserializa desde un diccionario"""
        # Crear instancia básica
        user_id = data["meta"]["user_id"]
        conversation_id = data["meta"]["conversation_id"]
        instance = cls(user_id, conversation_id)
        
        # Restaurar todos los campos
        instance.meta = data["meta"]
        instance.conversation = data["conversation"]
        instance.query = data["query"]
        instance.issues = data.get("issues", [])
        instance.execution = data.get("execution", instance.execution)
        instance.history = data.get("history", [])
        
        return instance
    
    def get_context_summary(self) -> str:
        """Genera un resumen del contexto actual para el agente"""
        summary_parts = []
        
        # Estado actual
        summary_parts.append(f"Estado: {self.conversation['status']}")
        
        # Tipo de consulta
        if self.query["type"]:
            summary_parts.append(f"Tipo de consulta: {self.query['type']}")
        
        # Tabla objetivo
        if self.query["table"]:
            summary_parts.append(f"Tabla: {self.query['table']}")
        
        # Filtros aplicados
        if self.query["filters"]:
            filters_str = ", ".join([f"{k}={v}" for k, v in self.query["filters"].items()])
            summary_parts.append(f"Filtros: {filters_str}")
        
        # Issues pendientes
        if self.issues:
            issues_str = ", ".join([i["type"] for i in self.issues])
            summary_parts.append(f"Issues: {issues_str}")
        
        # Pregunta pendiente
        if self.conversation["pending_question"]:
            summary_parts.append(f"Esperando respuesta a: {self.conversation['pending_question']}")
        
        return " | ".join(summary_parts)
    
    def __repr__(self):
        return f"<ConversationState {self.meta['conversation_id']} - {self.conversation['status']}>"
