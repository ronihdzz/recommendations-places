import os
from typing import List, Dict

import openai
from loguru import logger
from sqlalchemy import text

from db.posgresql.connection import get_db_context
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
    
    async def get_recommendations(self, description: str, limit: int = 5) -> RecommendationResponse:
        """
        Obtiene recomendaciones de lugares basado en una descripción de texto
        
        Args:
            description: Descripción del tipo de lugar que buscas
            limit: Número de recomendaciones (por defecto 5)
            
        Returns:
            RecommendationResponse con los lugares recomendados
        """
        try:
            # 1. Generar embedding de la descripción
            logger.info(f"Generando recomendaciones para: '{description}'")
            
            response = self.openai_client.embeddings.create(
                model=self.model,
                input=description
            )
            
            query_embedding = response.data[0].embedding
            
            # 2. Buscar lugares similares en la base de datos
            with get_db_context() as session:
                sql_query = text("""
                    SELECT 
                        id,
                        name,
                        category,
                        description,
                        rating,
                        price_level,
                        address,
                        vector_embedding <-> CAST(:query_embedding AS vector) as distance
                    FROM public.places 
                    WHERE vector_embedding IS NOT NULL
                      AND deleted_at IS NULL
                    ORDER BY distance
                    LIMIT :limit
                """)
                
                # Convertir el embedding a formato string para PostgreSQL
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                result = session.execute(sql_query, {
                    "query_embedding": embedding_str,
                    "limit": limit
                }).fetchall()
                
                # 3. Formatear resultados
                recommendations = []
                for row in result:
                    place_recommendation = PlaceRecommendation(
                        id=str(row.id),
                        name=row.name,
                        category=row.category,
                        description=row.description,
                        rating=float(row.rating) if row.rating else None,
                        price_level=row.price_level,
                        address=row.address,
                        similarity_score=round((1 - float(row.distance)) * 100, 1)  # Convertir distancia a porcentaje de similitud
                    )
                    recommendations.append(place_recommendation)
                
                logger.success(f"✅ Encontradas {len(recommendations)} recomendaciones")
                
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
