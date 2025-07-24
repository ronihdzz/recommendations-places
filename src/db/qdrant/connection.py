from typing import Optional
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
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
        
        # Log de configuración inicial
        logger.info(f"🔧 Configurando conexión Qdrant:")
        logger.info(f"   📍 URL: {self.url}")
        logger.info(f"   🔑 API Key configurada: {'Sí' if settings.QDRANT_API_KEY else 'No'}")
    
    @property
    def client(self) -> QdrantClient:
        """Obtiene el cliente de Qdrant, creándolo si es necesario"""
        if self._client is None:
            logger.info(f"🔌 Intentando establecer conexión con Qdrant...")
            try:
                self._client = QdrantClient(url=self.url, api_key=settings.QDRANT_API_KEY)
                
                # Verificar la conexión inmediatamente
                start_time = time.time()
                self._client.get_collections()
                connection_time = time.time() - start_time
                
                logger.success(f"✅ Conexión con Qdrant establecida exitosamente en {self.url}")
                logger.info(f"⏱️  Tiempo de conexión: {connection_time:.2f}s")
                
            except ConnectionError as e:
                logger.error(f"🚫 Error de conexión con Qdrant:")
                logger.error(f"   📍 URL intentada: {self.url}")
                logger.error(f"   🔥 Error: {type(e).__name__}: {e}")
                logger.error(f"   💡 Solución: Verifica que Qdrant esté ejecutándose en {self.url}")
                logger.error(f"   🐳 Docker: docker-compose up qdrant")
                raise
                
            except UnexpectedResponse as e:
                logger.error(f"🚫 Respuesta inesperada de Qdrant:")
                logger.error(f"   📍 URL: {self.url}")
                logger.error(f"   📄 Status: {getattr(e, 'status_code', 'N/A')}")
                logger.error(f"   📝 Contenido: {getattr(e, 'content', 'N/A')}")
                logger.error(f"   💡 Verifica la configuración de Qdrant")
                raise
                
            except Exception as e:
                logger.error(f"🚫 Error inesperado conectando con Qdrant:")
                logger.error(f"   📍 URL: {self.url}")
                logger.error(f"   🔥 Tipo: {type(e).__name__}")
                logger.error(f"   📝 Error: {e}")
                logger.error(f"   🔍 Verifica logs de Qdrant para más detalles")
                raise
                
        return self._client
    
    def close(self):
        """Cierra la conexión con Qdrant"""
        if self._client:
            try:
                self._client.close()
                self._client = None
                logger.info("🔌 Conexión con Qdrant cerrada exitosamente")
            except Exception as e:
                logger.warning(f"⚠️ Error al cerrar conexión con Qdrant: {e}")
    
    def is_connected(self) -> bool:
        """Verifica si la conexión con Qdrant está activa"""
        if self._client is None:
            logger.debug("🔍 Cliente Qdrant no inicializado")
            return False
            
        try:
            start_time = time.time()
            collections = self.client.get_collections()
            check_time = time.time() - start_time
            
            logger.debug(f"✅ Verificación de conexión exitosa ({check_time:.2f}s)")
            logger.debug(f"📊 Colecciones disponibles: {len(collections.collections)}")
            return True
            
        except ConnectionError as e:
            logger.error(f"🚫 Qdrant no está disponible:")
            logger.error(f"   📍 URL: {self.url}")
            logger.error(f"   🔥 Error: {e}")
            logger.error(f"   💡 Verifica que Qdrant esté ejecutándose")
            return False
            
        except Exception as e:
            logger.error(f"🚫 Error verificando conexión con Qdrant:")
            logger.error(f"   📍 URL: {self.url}")
            logger.error(f"   🔥 Tipo: {type(e).__name__}")
            logger.error(f"   📝 Error: {e}")
            return False

    def health_check(self) -> dict:
        """Realiza un chequeo completo de salud de Qdrant"""
        logger.info("🏥 Iniciando chequeo de salud de Qdrant...")
        
        health_status = {
            "connected": False,
            "url": self.url,
            "collections_count": 0,
            "response_time": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # Verificar conexión
            collections = self.client.get_collections()
            response_time = time.time() - start_time
            
            health_status.update({
                "connected": True,
                "collections_count": len(collections.collections),
                "response_time": round(response_time, 3)
            })
            
            logger.success("✅ Qdrant está funcionando correctamente")
            logger.info(f"   ⏱️  Tiempo de respuesta: {response_time:.3f}s")
            logger.info(f"   📊 Colecciones: {len(collections.collections)}")
            
        except Exception as e:
            health_status["error"] = str(e)
            logger.error(f"❌ Chequeo de salud falló: {e}")
            
        return health_status


# Instancia global de conexión
qdrant_connection = QdrantConnection()


def get_qdrant_client() -> QdrantClient:
    """Obtiene el cliente de Qdrant"""
    return qdrant_connection.client


def close_qdrant_connection():
    """Cierra la conexión global con Qdrant"""
    qdrant_connection.close()


def qdrant_health_check() -> dict:
    """Función de conveniencia para chequeo de salud"""
    return qdrant_connection.health_check() 