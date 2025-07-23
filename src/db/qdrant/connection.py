from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from loguru import logger
from core.settings import settings


class QdrantConnection:
    """Clase para manejar la conexión con Qdrant"""
    
    def __init__(self, url: str = None):
        """
        Inicializa la conexión con Qdrant
        
        Args:
            url: URL completa de Qdrant (usa settings por defecto)
        """
        self.url = url or settings.QDRANT_URL
        self._client: Optional[QdrantClient] = None
    
    @property
    def client(self) -> QdrantClient:
        """Obtiene el cliente de Qdrant, creándolo si es necesario"""
        if self._client is None:
            self._client = QdrantClient(url=self.url)
            logger.info(f"Conexión establecida con Qdrant en {self.url}")
        return self._client
    
    def close(self):
        """Cierra la conexión con Qdrant"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Conexión con Qdrant cerrada")
    
    def is_connected(self) -> bool:
        """Verifica si la conexión con Qdrant está activa"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Error al verificar conexión con Qdrant: {e}")
            return False


# Instancia global de conexión
qdrant_connection = QdrantConnection()


def get_qdrant_client() -> QdrantClient:
    """Obtiene el cliente de Qdrant"""
    return qdrant_connection.client


def close_qdrant_connection():
    """Cierra la conexión global con Qdrant"""
    qdrant_connection.close() 