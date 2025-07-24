import os
import time
from typing import List, Dict
from uuid import UUID

import openai
from loguru import logger

from db.posgresql.connection import get_db_context
from db.posgresql.repository.places import PlaceRepository
from db.qdrant.repository import PlaceEmbeddingRepository
from db.qdrant.connection import qdrant_health_check
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
        
        logger.info(f"🤖 Servicio de recomendaciones inicializado:")
        logger.info(f"   🔧 Modelo OpenAI: {self.model}")
        logger.info(f"   📊 Colección Qdrant: {self.qdrant_repo.collection_name}")
    
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
        start_time = time.time()
        logger.info(f"🔍 Generando recomendaciones para: '{description}'")
        logger.info(f"   🎯 Límite solicitado: {limit}")
        
        try:
            # Pre-verificación: Estado de Qdrant
            logger.debug("🏥 Verificando estado de Qdrant...")
            health = qdrant_health_check()
            if not health.get("connected", False):
                error_msg = f"Qdrant no está disponible: {health.get('error', 'Conexión fallida')}"
                logger.error(f"🚫 {error_msg}")
                logger.error(f"   📍 URL: {health.get('url', 'N/A')}")
                logger.error(f"   💡 Verifica que Qdrant esté ejecutándose")
                
                return RecommendationResponse(
                    query=description,
                    total_found=0,
                    recommendations=[]
                )
            
            logger.debug(f"✅ Qdrant disponible ({health.get('response_time', 0):.3f}s)")
            
            # 1. Convertir el texto del usuario en embedding
            logger.debug("🧠 Generando embedding con OpenAI...")
            embedding_start = time.time()
            
            try:
                response = self.openai_client.embeddings.create(
                    model=self.model,
                    input=description
                )
                
                query_embedding = response.data[0].embedding
                embedding_time = time.time() - embedding_start
                
                logger.success(f"✅ Embedding generado ({embedding_time:.3f}s)")
                logger.debug(f"   📏 Dimensiones: {len(query_embedding)}")
                
            except Exception as openai_error:
                logger.error(f"🚫 Error generando embedding con OpenAI:")
                logger.error(f"   🔧 Modelo: {self.model}")
                logger.error(f"   📝 Input: '{description[:100]}{'...' if len(description) > 100 else ''}'")
                logger.error(f"   🔥 Error: {openai_error}")
                raise
            
            # 2. Buscar en Qdrant los lugares más similares
            logger.debug("🎯 Buscando lugares similares en Qdrant...")
            
            try:
                similar_places = self.qdrant_repo.search_similar_places(
                    query_embedding=query_embedding,
                    limit=limit,
                    score_threshold=0.1  # Solo lugares con al menos 10% de similitud
                )
                
                logger.info(f"📊 Qdrant encontró {len(similar_places)} lugares similares")
                
                if not similar_places:
                    logger.warning("⚠️ No se encontraron lugares similares en Qdrant")
                    logger.warning("   💡 Posibles causas:")
                    logger.warning("   - Colección vacía o sin datos")
                    logger.warning("   - Score threshold muy alto")
                    logger.warning("   - Embedding query muy específico")
                    
                    return RecommendationResponse(
                        query=description,
                        total_found=0,
                        recommendations=[]
                    )
                    
            except Exception as qdrant_error:
                logger.error(f"🚫 Error en búsqueda vectorial Qdrant:")
                logger.error(f"   📊 Colección: {self.qdrant_repo.collection_name}")
                logger.error(f"   🔥 Tipo: {type(qdrant_error).__name__}")
                logger.error(f"   📝 Error: {qdrant_error}")
                
                # Información adicional de contexto
                if "Connection refused" in str(qdrant_error):
                    logger.error(f"   💡 Qdrant parece no estar ejecutándose")
                    logger.error(f"   🔧 Ejecuta: docker-compose up qdrant")
                elif "404" in str(qdrant_error):
                    logger.error(f"   💡 La colección '{self.qdrant_repo.collection_name}' no existe")
                    logger.error(f"   🔧 Ejecuta el script de embeddings para crearla")
                
                raise
            
            # 3. Obtener los IDs de los lugares más parecidos
            place_ids = [result["id"] for result in similar_places]
            logger.debug(f"🆔 IDs encontrados: {place_ids}")
            
            # 4. Consultar PostgreSQL para obtener los datos completos
            logger.debug("🗄️ Consultando datos completos en PostgreSQL...")
            db_start = time.time()
            
            try:
                with get_db_context() as session:
                    place_repo = PlaceRepository(session)
                    places = place_repo.get_places_by_ids(place_ids)
                    
                db_time = time.time() - db_start
                logger.debug(f"✅ PostgreSQL consultado ({db_time:.3f}s)")
                logger.info(f"📋 Obtenidos {len(places)} lugares de PostgreSQL")
                
                if len(places) != len(place_ids):
                    logger.warning(f"⚠️ Discrepancia en datos:")
                    logger.warning(f"   🎯 IDs solicitados: {len(place_ids)}")
                    logger.warning(f"   📋 Places encontrados: {len(places)}")
                    
            except Exception as db_error:
                logger.error(f"🚫 Error consultando PostgreSQL:")
                logger.error(f"   🆔 IDs buscados: {place_ids}")
                logger.error(f"   🔥 Error: {db_error}")
                raise
            
            # 5. Combinar datos de similitud con datos de PostgreSQL
            logger.debug("🔗 Combinando datos de Qdrant y PostgreSQL...")
            
            # Crear mapa de scores por ID
            score_map = {result["id"]: result["score"] for result in similar_places}
            
            recommendations = []
            for place in places:
                place_id = str(place.id)
                similarity_score = score_map.get(place_id, 0.0)
                
                recommendation = PlaceRecommendation(
                    id=place.id,
                    name=place.name,
                    description=place.description,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    category=place.category,
                    rating=place.rating,
                    price_level=place.price_level,
                    price_average=place.price_average,
                    price_currency=place.price_currency,
                    address=place.address,
                    similarity_score=similarity_score
                )
                recommendations.append(recommendation)
            
            # Ordenar por score de similitud (ya debería estar ordenado, pero por seguridad)
            recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
            
            total_time = time.time() - start_time
            
            logger.success(f"✅ Recomendaciones generadas exitosamente!")
            logger.info(f"   ⏱️  Tiempo total: {total_time:.3f}s")
            logger.info(f"   📊 Resultados: {len(recommendations)}")
            
            if recommendations:
                best_score = recommendations[0].similarity_score
                worst_score = recommendations[-1].similarity_score
                logger.info(f"   🎯 Score rango: {worst_score:.3f} - {best_score:.3f}")
                
                # Log de los primeros resultados
                for i, rec in enumerate(recommendations[:3]):
                    logger.debug(f"   #{i+1}: {rec.name} (score: {rec.similarity_score:.3f})")
            
            # 5. Retornar resultados ordenados por relevancia (ya están ordenados por Qdrant)
            return RecommendationResponse(
                query=description,
                total_found=len(recommendations),
                recommendations=recommendations
            )
                
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"❌ Error generando recomendaciones ({total_time:.3f}s):")
            logger.error(f"   📝 Query: '{description}'")
            logger.error(f"   🔥 Tipo: {type(e).__name__}")
            logger.error(f"   📄 Error: {e}")
            
            # Información adicional de contexto para debugging
            logger.error(f"   🔧 Contexto del sistema:")
            logger.error(f"      - Modelo OpenAI: {self.model}")
            logger.error(f"      - Colección Qdrant: {self.qdrant_repo.collection_name}")
            
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
