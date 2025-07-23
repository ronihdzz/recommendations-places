#!/usr/bin/env python3
"""
Generador de embeddings para lugares usando OpenAI y almacenamiento en Qdrant
Versión actualizada que reemplaza pgvector con Qdrant
"""

import os
import re
import time
from typing import Optional, List
from decimal import Decimal

import openai
from loguru import logger

from db.posgresql.connection import get_db_context
from db.posgresql.models.public.places import Place
from db.posgresql.repository.places import PlaceRepository
from db.qdrant.repository import PlaceEmbeddingRepository
from core.settings import settings


class PlaceEmbeddingQdrantGenerator:
    """Generador de embeddings para lugares usando OpenAI text-embedding-3-small y Qdrant"""
    
    def __init__(self, openai_api_key: str):
        """
        Inicializa el generador de embeddings
        
        Args:
            openai_api_key: Clave API de OpenAI
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = "text-embedding-3-small"
        self.max_retries = 3
        self.retry_delay = 1  # segundos
        
        # Inicializar repositorio de Qdrant
        self.qdrant_repo = PlaceEmbeddingRepository()
        
        # Crear colección si no existe
        self.qdrant_repo.create_collection()
        
    def extract_neighborhood_from_address(self, address: str) -> str:
        """
        Extrae la zona o colonia de la dirección
        
        Args:
            address: Dirección completa
            
        Returns:
            Zona o colonia extraída, o cadena vacía si no se encuentra
        """
        if not address:
            return ""
        
        # Patrones comunes para identificar colonias/zonas en México
        patterns = [
            r"(?:Colonia|Col\.?)\s+([^,\n]+)",
            r"(?:Zona|Z\.?)\s+([^,\n]+)", 
            r"(?:Fraccionamiento|Fracc\.?)\s+([^,\n]+)",
            r"(?:Barrio|B\.?)\s+([^,\n]+)",
            r"(?:Delegación|Del\.?)\s+([^,\n]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                neighborhood = match.group(1).strip()
                # Limpiar caracteres comunes no deseados
                neighborhood = re.sub(r'[.,;]$', '', neighborhood)
                return neighborhood
        
        return ""
    
    def format_rating(self, rating: Decimal) -> str:
        """
        Formatea la calificación de manera descriptiva
        
        Args:
            rating: Calificación numérica
            
        Returns:
            Descripción textual de la calificación
        """
        if rating is None:
            return ""
        
        rating_float = float(rating)
        
        if rating_float >= 4.5:
            return "excelente calificación"
        elif rating_float >= 4.0:
            return "muy buena calificación"
        elif rating_float >= 3.5:
            return "buena calificación"
        elif rating_float >= 3.0:
            return "calificación promedio"
        else:
            return "calificación regular"
    
    def format_price_level(self, price_level: str) -> str:
        """
        Formatea el nivel de precios de manera descriptiva
        
        Args:
            price_level: Nivel de precios (LOW, MEDIUM, HIGH, etc.)
            
        Returns:
            Descripción textual del nivel de precios
        """
        if not price_level:
            return ""
        
        price_mapping = {
            "LOW": "económico",
            "MEDIUM": "moderado", 
            "HIGH": "alto",
            "PREMIUM": "premium"
        }
        
        return price_mapping.get(price_level.upper(), price_level.lower())
    
    def generate_enriched_text(self, place: Place) -> str:
        """
        Genera texto enriquecido para un lugar
        
        Args:
            place: Objeto Place de la base de datos
            
        Returns:
            Texto enriquecido listo para generar embedding
        """
        # Extraer componentes
        name = place.name or ""
        category = place.category or ""
        description = place.description or ""
        rating_text = self.format_rating(place.rating)
        price_text = self.format_price_level(place.price_level)
        neighborhood = self.extract_neighborhood_from_address(place.address or "")
        
        # Construir texto enriquecido con buena redacción
        text_parts = []
        
        # Introducción principal
        if category:
            text_parts.append(f"{name} es un {category}")
        else:
            text_parts.append(f"{name}")
        
        # Agregar ubicación si está disponible
        if neighborhood:
            text_parts.append(f"ubicado en {neighborhood}")
        
        # Agregar descripción si está disponible
        if description:
            text_parts.append(f". {description}")
        else:
            text_parts.append(".")
        
        # Agregar información de calificación
        if rating_text:
            text_parts.append(f" Este lugar tiene una {rating_text}")
            
        # Agregar información de precios
        if price_text:
            text_parts.append(f" y maneja precios de rango {price_text}")
        
        # Unir todas las partes
        enriched_text = "".join(text_parts)
        
        # Limpiar espacios extra y caracteres especiales
        enriched_text = re.sub(r'\s+', ' ', enriched_text)
        enriched_text = enriched_text.strip()
        
        logger.debug(f"Texto generado para {name}: {enriched_text}")
        return enriched_text
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Genera embedding usando OpenAI text-embedding-3-small
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            Lista de valores float del embedding, o None si falla
        """
        for attempt in range(self.max_retries):
            try:
                response = self.openai_client.embeddings.create(
                    model=self.model,
                    input=text
                )
                
                embedding = response.data[0].embedding
                logger.debug(f"Embedding generado exitosamente. Dimensiones: {len(embedding)}")
                return embedding
                
            except Exception as e:
                logger.warning(f"Error generando embedding (intento {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Backoff exponencial
                else:
                    logger.error(f"Falló generar embedding después de {self.max_retries} intentos")
                    return None
    
    def save_embedding_to_qdrant(self, place: Place, embedding: List[float]) -> bool:
        """
        Guarda el embedding de un lugar en Qdrant
        
        Args:
            place: Objeto Place de la base de datos
            embedding: Vector embedding
            
        Returns:
            True si fue exitoso, False si no
        """
        try:
            # Preparar metadata
            metadata = {
                "name": place.name,
                "description": place.description,
                "latitude": float(place.latitude) if place.latitude else None,
                "longitude": float(place.longitude) if place.longitude else None,
                "category": place.category,
                "rating": float(place.rating) if place.rating else None,
                "price_level": place.price_level,
                "price_average": float(place.price_average) if place.price_average else None,
                "price_currency": place.price_currency,
                "address": place.address,
                "created_at": place.created_at.isoformat() if place.created_at else None,
                "updated_at": place.updated_at.isoformat() if place.updated_at else None
            }
            
            # Guardar en Qdrant
            self.qdrant_repo.upsert_embedding(
                place_id=str(place.id),
                embedding=embedding,
                metadata=metadata
            )
            
            logger.debug(f"Embedding guardado en Qdrant para lugar {place.id}")
            return True
                    
        except Exception as e:
            logger.error(f"Error guardando embedding en Qdrant para lugar {place.id}: {e}")
            return False
    
    def check_if_embedding_exists(self, place_id: str) -> bool:
        """
        Verifica si ya existe un embedding para el lugar en Qdrant
        
        Args:
            place_id: ID del lugar
            
        Returns:
            True si existe, False si no
        """
        try:
            # Intentar obtener el punto de Qdrant
            points = self.qdrant_repo.client.retrieve(
                collection_name=self.qdrant_repo.collection_name,
                ids=[place_id]
            )
            
            return len(points) > 0
            
        except Exception as e:
            logger.debug(f"No se encontró embedding para lugar {place_id}: {e}")
            return False
    
    def process_all_places(self, batch_size: int = 10, skip_existing: bool = True) -> dict:
        """
        Procesa todos los lugares y genera sus embeddings
        
        Args:
            batch_size: Número de lugares a procesar por lote
            skip_existing: Si saltar lugares que ya tienen embedding en Qdrant
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        stats = {
            "total_places": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            with get_db_context() as session:
                repository = PlaceRepository(session)
                
                # Obtener conteo total
                stats["total_places"] = repository.count()
                logger.info(f"Iniciando procesamiento de {stats['total_places']} lugares")
                logger.info(f"Almacenamiento: Qdrant (colección: {self.qdrant_repo.collection_name})")
                
                # Procesar en lotes
                offset = 0
                while True:
                    places = repository.get_all(skip=offset, limit=batch_size)
                    if not places:
                        break
                    
                    logger.info(f"Procesando lote {offset//batch_size + 1}: lugares {offset + 1}-{offset + len(places)}")
                    
                    for place in places:
                        stats["processed"] += 1
                        
                        try:
                            # Verificar si ya tiene embedding en Qdrant
                            if skip_existing and self.check_if_embedding_exists(str(place.id)):
                                logger.debug(f"Lugar {place.name} ya tiene embedding en Qdrant, saltando...")
                                stats["skipped"] += 1
                                continue
                            
                            # Generar texto enriquecido
                            enriched_text = self.generate_enriched_text(place)
                            
                            if not enriched_text:
                                logger.warning(f"No se pudo generar texto para {place.name}")
                                stats["failed"] += 1
                                continue
                            
                            # Generar embedding
                            embedding = self.generate_embedding(enriched_text)
                            
                            if not embedding:
                                logger.error(f"No se pudo generar embedding para {place.name}")
                                stats["failed"] += 1
                                continue
                            
                            # Guardar en Qdrant
                            if self.save_embedding_to_qdrant(place, embedding):
                                stats["successful"] += 1
                                logger.info(f"✅ Procesado exitosamente: {place.name}")
                            else:
                                stats["failed"] += 1
                                logger.error(f"❌ Error guardando en Qdrant: {place.name}")
                            
                            # Pequeña pausa para evitar rate limiting
                            time.sleep(0.1)
                            
                        except Exception as e:
                            stats["failed"] += 1
                            logger.error(f"❌ Error procesando lugar {place.name}: {e}")
                    
                    offset += batch_size
                    
                    # Mostrar progreso cada cierto número de lotes
                    if (offset // batch_size) % 5 == 0:
                        success_rate = (stats["successful"] / stats["processed"]) * 100 if stats["processed"] > 0 else 0
                        logger.info(f"Progreso: {stats['processed']}/{stats['total_places']} ({success_rate:.1f}% exitoso)")
        
        except Exception as e:
            logger.error(f"Error durante el procesamiento: {e}")
        
        return stats
    
    def get_collection_stats(self) -> dict:
        """
        Obtiene estadísticas de la colección de Qdrant
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            return self.qdrant_repo.get_collection_info()
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de Qdrant: {e}")
            return {}


def main():
    """Función principal"""
    logger.info("🚀 Iniciando generación de embeddings para lugares (Qdrant)")
    
    # Obtener API key de OpenAI desde configuración
    openai_api_key = settings.OPENAI_API_KEY
    if not openai_api_key:
        logger.error("❌ OPENAI_API_KEY no está configurada en las variables de entorno")
        return
    
    # Crear generador
    generator = PlaceEmbeddingQdrantGenerator(openai_api_key)
    
    # Mostrar estadísticas iniciales de Qdrant
    initial_stats = generator.get_collection_stats()
    if initial_stats:
        logger.info(f"📊 Estado inicial de Qdrant:")
        logger.info(f"   - Colección: {initial_stats.get('name', 'N/A')}")
        logger.info(f"   - Puntos existentes: {initial_stats.get('points_count', 0)}")
    
    # Procesar todos los lugares
    stats = generator.process_all_places(batch_size=10, skip_existing=True)
    
    # Mostrar estadísticas finales de Qdrant
    final_stats = generator.get_collection_stats()
    
    # Mostrar resumen final
    logger.info("📊 Resumen final:")
    logger.info(f"  Total de lugares en PostgreSQL: {stats['total_places']}")
    logger.info(f"  Lugares procesados: {stats['processed']}")
    logger.info(f"  Exitosos: {stats['successful']}")
    logger.info(f"  Fallidos: {stats['failed']}")
    logger.info(f"  Saltados (ya existían): {stats['skipped']}")
    
    if final_stats:
        logger.info(f"  Total en Qdrant: {final_stats.get('points_count', 0)}")
    
    if stats['processed'] > 0:
        success_rate = (stats['successful'] / stats['processed']) * 100
        logger.info(f"  Tasa de éxito: {success_rate:.1f}%")
    
    if stats['successful'] > 0:
        logger.success("✅ Proceso completado exitosamente")
        logger.info("💡 Los embeddings están ahora disponibles en Qdrant para búsquedas de similitud")
    else:
        logger.warning("⚠️ No se procesó ningún lugar exitosamente")


if __name__ == "__main__":
    main() 