import os
from typing import List, Dict
from uuid import UUID

import openai
from loguru import logger

from db.posgresql.connection import get_db_context
from db.posgresql.repository.places import PlaceRepository
from db.qdrant.repository import PlaceEmbeddingRepository
from .schema import RecommendationResponse, PlaceRecommendation


class PlaceRecommendationService:
    """Servicio para recomendaciones de lugares basado en descripciones de texto"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Inicializa el servicio de recomendaciones
        
        Args:
            openai_api_key: Clave API de OpenAI (opcional, se puede obtener de env)
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY no encontrada. Configúrala como variable de entorno o pásala como parámetro.")
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        
        # Inicializar repositorio de Qdrant
        self.qdrant_repo = PlaceEmbeddingRepository()
    
    async def get_recommendations(self, description: str, limit: int = 5) -> RecommendationResponse:
        """
        Obtiene recomendaciones de lugares basado en una descripción de texto
        
        FLUJO:
        1. Convierte el texto del usuario en embedding
        2. Busca en Qdrant los lugares más similares
        3. Obtiene los IDs de los lugares más parecidos
        4. Consulta PostgreSQL para obtener los datos completos
        5. Retorna los resultados ordenados por relevancia
        
        Args:
            description: Descripción del tipo de lugar que buscas
            limit: Número de recomendaciones (por defecto 5)
            
        Returns:
            RecommendationResponse con los lugares recomendados
        """
        try:
            # 1. Convertir el texto del usuario en embedding
            logger.info(f"🔍 Generando recomendaciones para: '{description}'")
            
            response = self.openai_client.embeddings.create(
                model=self.model,
                input=description
            )
            
            query_embedding = response.data[0].embedding
            logger.debug(f"✅ Embedding generado con {len(query_embedding)} dimensiones")
            
            # 2. Buscar en Qdrant los lugares más similares
            similar_places = self.qdrant_repo.search_similar_places(
                query_embedding=query_embedding,
                limit=limit,
                score_threshold=0.1  # Solo lugares con al menos 70% de similitud
            )
            
            if not similar_places:
                logger.info("❌ No se encontraron lugares similares en Qdrant")
                return RecommendationResponse(
                    query=description,
                    total_found=0,
                    recommendations=[]
                )
            
            # 3. Obtener los IDs de los lugares más parecidos
            place_ids = [result["id"] for result in similar_places]
            logger.info(f"🎯 Encontrados {len(place_ids)} lugares similares en Qdrant")
            
            # 4. Consultar PostgreSQL para obtener los datos completos
            with get_db_context() as session:
                place_repository = PlaceRepository(session)
                recommendations = []
                
                for result in similar_places:
                    place_id = result["id"]
                    similarity_score = result["score"]
                    
                    try:
                        # Convertir string ID a UUID
                        place_uuid = UUID(place_id)
                        
                        # Obtener datos completos del lugar desde PostgreSQL
                        place = place_repository.get_by_id(place_uuid)
                        
                        if place:
                            place_recommendation = PlaceRecommendation(
                                id=str(place.id),
                                name=place.name,
                                category=place.category,
                                description=place.description,
                                rating=float(place.rating) if place.rating else None,
                                price_level=place.price_level,
                                address=place.address,
                                similarity_score=round(similarity_score * 100, 1)
                            )
                            recommendations.append(place_recommendation)
                            logger.debug(f"✅ Lugar encontrado: {place.name} (similitud: {similarity_score:.3f})")
                        else:
                            logger.warning(f"⚠️ Lugar {place_id} no encontrado en PostgreSQL")
                            
                    except Exception as e:
                        logger.error(f"❌ Error procesando lugar {place_id}: {e}")
                        continue
                
                logger.success(f"✅ Se encontraron {len(recommendations)} recomendaciones válidas")
                
                # 5. Retornar resultados ordenados por relevancia (ya están ordenados por Qdrant)
                return RecommendationResponse(
                    query=description,
                    total_found=len(recommendations),
                    recommendations=recommendations
                )
                
        except Exception as e:
            logger.error(f"❌ Error generando recomendaciones: {e}")
            # En caso de error, devolver respuesta vacía
            return RecommendationResponse(
                query=description,
                total_found=0,
                recommendations=[]
            )


# Singleton para reutilizar la instancia del servicio
_recommendation_service = None

def get_recommendation_service() -> PlaceRecommendationService:
    """
    Obtiene una instancia singleton del servicio de recomendaciones
    
    Returns:
        PlaceRecommendationService: Instancia del servicio
    """
    global _recommendation_service
    if _recommendation_service is None:
        _recommendation_service = PlaceRecommendationService()
    return _recommendation_service
