from typing import List, Dict, Any, Optional
from uuid import UUID
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
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
        
    def create_collection(self):
        """Crea la colección de embeddings si no existe"""
        try:
            # Verificar si la colección ya existe
            collections = self.client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if self.collection_name not in existing_collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Colección '{self.collection_name}' creada exitosamente")
            else:
                logger.info(f"Colección '{self.collection_name}' ya existe")
                
        except Exception as e:
            logger.error(f"Error al crear colección: {e}")
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
            point = PointStruct(
                id=place_id,
                vector=embedding,
                payload=metadata
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"Embedding upserted para lugar ID: {place_id}")
            
        except Exception as e:
            logger.error(f"Error al hacer upsert del embedding: {e}")
            raise
    
    def search_similar_places(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca lugares similares basado en un embedding de consulta
        
        Args:
            query_embedding: Vector de embedding de la consulta
            limit: Número máximo de resultados
            score_threshold: Umbral mínimo de similitud
            filters: Filtros adicionales para la búsqueda
            
        Returns:
            Lista de lugares similares con metadatos y scores
        """
        try:
            # Construir filtros si se proporcionan
            query_filter = None
            if filters:
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
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Formatear resultados
            results = []
            for result in search_results:
                results.append({
                    "place_id": result.id,
                    "score": result.score,
                    "metadata": result.payload
                })
            
            logger.info(f"Búsqueda completada: {len(results)} lugares encontrados")
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de similitud: {e}")
            raise
    
    def delete_embedding(self, place_id: str):
        """
        Elimina un embedding de lugar
        
        Args:
            place_id: ID del lugar a eliminar
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[place_id]
            )
            logger.info(f"Embedding eliminado para lugar ID: {place_id}")
            
        except Exception as e:
            logger.error(f"Error al eliminar embedding: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la colección
        
        Returns:
            Información de la colección
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,  # Usar el nombre que ya tenemos
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error al obtener información de la colección: {e}")
            raise 