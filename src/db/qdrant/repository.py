from typing import List, Dict, Any, Optional
from uuid import UUID
import time
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
from loguru import logger
from core.settings import settings
from .connection import get_qdrant_client


class PlaceEmbeddingRepository:
    """Repositorio para manejar embeddings de lugares en Qdrant"""
    
    def __init__(self, collection_name: str = None):
        """
        Inicializa el repositorio
        
        Args:
            collection_name: Nombre de la colección en Qdrant (usa settings por defecto)
        """
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.client = get_qdrant_client()
        self.vector_size = 1536  # OpenAI text-embedding-3-small dimensions
        
        logger.debug(f"🗄️ Repositorio Qdrant inicializado:")
        logger.debug(f"   📊 Colección: {self.collection_name}")
        logger.debug(f"   📏 Tamaño vector: {self.vector_size}")
        
    def create_collection(self):
        """Crea la colección de embeddings si no existe"""
        try:
            logger.info(f"🔧 Verificando colección '{self.collection_name}'...")
            
            # Verificar si la colección ya existe
            collections = self.client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            logger.debug(f"📊 Colecciones existentes: {existing_collections}")
            
            if self.collection_name not in existing_collections:
                logger.info(f"📝 Creando nueva colección '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.success(f"✅ Colección '{self.collection_name}' creada exitosamente")
            else:
                logger.info(f"✅ Colección '{self.collection_name}' ya existe")
                
        except Exception as e:
            logger.error(f"❌ Error al crear colección '{self.collection_name}':")
            logger.error(f"   🔥 Tipo: {type(e).__name__}")
            logger.error(f"   📝 Error: {e}")
            raise
    
    def upsert_embedding(self, place_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """
        Inserta o actualiza un embedding de lugar
        
        Args:
            place_id: ID único del lugar
            embedding: Vector de embedding
            metadata: Metadatos del lugar (nombre, categoría, etc.)
        """
        try:
            logger.debug(f"💾 Guardando embedding para lugar ID: {place_id}")
            
            point = PointStruct(
                id=place_id,
                vector=embedding,
                payload=metadata
            )
            
            start_time = time.time()
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            upsert_time = time.time() - start_time
            
            logger.debug(f"✅ Embedding guardado ({upsert_time:.3f}s) - ID: {place_id}")
            
        except Exception as e:
            logger.error(f"❌ Error al hacer upsert del embedding:")
            logger.error(f"   🆔 Place ID: {place_id}")
            logger.error(f"   📊 Colección: {self.collection_name}")
            logger.error(f"   🔥 Tipo: {type(e).__name__}")
            logger.error(f"   📝 Error: {e}")
            raise
    
    def search_similar_places(
        self, 
        query_embedding: List[float], 
        limit: int = 5, 
        score_threshold: float = 0.0,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca lugares similares basado en un embedding de consulta
        
        Args:
            query_embedding: Vector de embedding para buscar similares
            limit: Número máximo de resultados
            score_threshold: Umbral mínimo de similitud (0.0 - 1.0)
            filters: Filtros adicionales para la búsqueda
            
        Returns:
            Lista de diccionarios con id, score y payload de lugares similares
        """
        logger.info(f"🔍 Iniciando búsqueda de lugares similares:")
        logger.info(f"   📊 Colección: {self.collection_name}")
        logger.info(f"   📏 Dimensiones embedding: {len(query_embedding)}")
        logger.info(f"   🎯 Límite: {limit}")
        logger.info(f"   📊 Umbral score: {score_threshold}")
        logger.info(f"   🔧 Filtros: {filters if filters else 'Ninguno'}")
        
        try:
            # Verificar dimensiones del embedding
            if len(query_embedding) != self.vector_size:
                raise ValueError(f"Embedding debe tener {self.vector_size} dimensiones, recibido: {len(query_embedding)}")
            
            # Construir filtros si se proporcionan
            query_filter = None
            if filters:
                logger.debug(f"🔧 Construyendo filtros: {filters}")
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Realizar búsqueda
            logger.debug(f"🚀 Ejecutando búsqueda vectorial...")
            start_time = time.time()
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True  # Incluir metadatos en los resultados
            )
            
            search_time = time.time() - start_time
            logger.info(f"⚡ Búsqueda completada en {search_time:.3f}s")
            
            # Formatear resultados
            results = []
            for i, scored_point in enumerate(search_result):
                result = {
                    "id": scored_point.id,
                    "score": scored_point.score,
                    "payload": scored_point.payload
                }
                results.append(result)
                
                logger.debug(f"   🎯 #{i+1}: ID={scored_point.id}, Score={scored_point.score:.4f}")
            
            logger.success(f"✅ Encontrados {len(results)} lugares similares (threshold: {score_threshold})")
            
            if len(results) == 0:
                logger.warning(f"⚠️ No se encontraron resultados:")
                logger.warning(f"   🎯 Considera reducir el score_threshold (actual: {score_threshold})")
                logger.warning(f"   📊 Verifica que la colección tenga datos")
                
                # Información adicional de debug
                try:
                    collection_info = self.client.get_collection(self.collection_name)
                    logger.warning(f"   📈 Puntos en colección: {collection_info.points_count}")
                except Exception as debug_e:
                    logger.warning(f"   ❓ No se pudo obtener info de colección: {debug_e}")
            
            return results
            
        except ConnectionError as e:
            logger.error(f"🚫 Error de conexión durante búsqueda vectorial:")
            logger.error(f"   📊 Colección: {self.collection_name}")
            logger.error(f"   🌐 URL Qdrant: {getattr(self.client, '_client', {}).get('url', 'N/A')}")
            logger.error(f"   🔥 Error: {e}")
            logger.error(f"   💡 Verifica que Qdrant esté ejecutándose y accesible")
            logger.error(f"   🔧 Comando: docker-compose up qdrant")
            raise
            
        except UnexpectedResponse as e:
            logger.error(f"🚫 Respuesta inesperada de Qdrant durante búsqueda:")
            logger.error(f"   📊 Colección: {self.collection_name}")
            logger.error(f"   📄 Status: {getattr(e, 'status_code', 'N/A')}")
            logger.error(f"   📝 Contenido: {getattr(e, 'content', 'N/A')}")
            logger.error(f"   💡 Verifica la configuración y estado de Qdrant")
            raise
            
        except ValueError as e:
            logger.error(f"🚫 Error de validación en búsqueda:")
            logger.error(f"   📏 Dimensiones esperadas: {self.vector_size}")
            logger.error(f"   📏 Dimensiones recibidas: {len(query_embedding) if query_embedding else 'N/A'}")
            logger.error(f"   📝 Error: {e}")
            raise
            
        except Exception as e:
            logger.error(f"🚫 Error inesperado en búsqueda de lugares similares:")
            logger.error(f"   📊 Colección: {self.collection_name}")
            logger.error(f"   🔥 Tipo: {type(e).__name__}")
            logger.error(f"   📝 Error: {e}")
            logger.error(f"   🔍 Stack trace completo disponible en logs debug")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre la colección
        
        Returns:
            Diccionario con información de la colección
        """
        try:
            logger.debug(f"📊 Obteniendo información de colección '{self.collection_name}'...")
            
            collection_info = self.client.get_collection(self.collection_name)
            
            info_dict = {
                "name": self.collection_name,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "disk_data_size": collection_info.disk_data_size,
                "ram_data_size": collection_info.ram_data_size,
                "config": {
                    "vector_size": collection_info.config.params.vectors.size,
                    "distance": collection_info.config.params.vectors.distance.value
                }
            }
            
            logger.debug(f"✅ Info obtenida - Puntos: {info_dict['points_count']}")
            return info_dict
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo información de colección:")
            logger.error(f"   📊 Colección: {self.collection_name}")
            logger.error(f"   🔥 Error: {e}")
            raise
    
    def delete_embedding(self, place_id: str) -> bool:
        """
        Elimina un embedding de lugar
        
        Args:
            place_id: ID del lugar a eliminar
            
        Returns:
            True si fue exitoso, False si no
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[place_id]
            )
            logger.info(f"Embedding eliminado para lugar ID: {place_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando embedding: {e}")
            return False 