import os
import re
import time
from typing import Optional, List
from decimal import Decimal

import openai
from loguru import logger
from sqlalchemy import text

from db.posgresql.connection import get_db_context
from db.posgresql.models.public.places import Place
from db.posgresql.repository.places import PlaceRepository
from core.settings import settings


class PlaceEmbeddingGenerator:
    """Generador de embeddings para lugares usando OpenAI text-embedding-3-small"""
    
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
            r"(?:Municipio|Mpio\.?)\s+([^,\n]+)",
            # Buscar después de la primera coma (formato común: "Calle, Colonia, Ciudad")
            r",\s*([^,\n]+?)(?:,|\s*\d{5}|\s*C\.?P\.?|\s*$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                neighborhood = match.group(1).strip()
                # Limpiar números de código postal y palabras comunes
                neighborhood = re.sub(r'\b\d{5}\b', '', neighborhood)
                neighborhood = re.sub(r'\b(?:C\.?P\.?|CP)\b', '', neighborhood, flags=re.IGNORECASE)
                return neighborhood.strip()
        
        # Si no se encuentra patrón específico, tomar el segmento después de la primera coma
        parts = address.split(',')
        if len(parts) > 1:
            return parts[1].strip()
        
        return ""
    
    def format_price_level(self, price_level: str) -> str:
        """
        Formatea el nivel de precio para texto legible
        
        Args:
            price_level: Nivel de precio (ej: "$", "$$", "$$$")
            
        Returns:
            Descripción legible del nivel de precio
        """
        if not price_level:
            return ""
        
        price_mapping = {
            "$": "económico",
            "$$": "precio medio", 
            "$$$": "precio alto",
            "$$$$": "precio muy alto"
        }
        
        return price_mapping.get(price_level, price_level)
    
    def format_rating(self, rating: Optional[Decimal]) -> str:
        """
        Formatea la calificación para texto legible
        
        Args:
            rating: Calificación numérica
            
        Returns:
            Descripción legible de la calificación
        """
        if not rating:
            return ""
        
        rating_float = float(rating)
        
        if rating_float >= 4.5:
            return f"excelente calificación de {rating_float}"
        elif rating_float >= 4.0:
            return f"muy buena calificación de {rating_float}"
        elif rating_float >= 3.5:
            return f"buena calificación de {rating_float}"
        elif rating_float >= 3.0:
            return f"calificación regular de {rating_float}"
        else:
            return f"calificación de {rating_float}"
    
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
    
    def update_place_embedding(self, place_id: str, embedding: List[float]) -> bool:
        """
        Actualiza el embedding de un lugar en la base de datos
        
        Args:
            place_id: ID del lugar
            embedding: Vector embedding
            
        Returns:
            True si fue exitoso, False si no
        """
        try:
            with get_db_context() as session:
                result = session.execute(
                    text("UPDATE public.places SET vector_embedding = :embedding WHERE id = :place_id"),
                    {"embedding": embedding, "place_id": place_id}
                )
                session.commit()
                
                if result.rowcount > 0:
                    logger.debug(f"Embedding actualizado para lugar {place_id}")
                    return True
                else:
                    logger.warning(f"No se encontró lugar con ID {place_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error actualizando embedding para lugar {place_id}: {e}")
            return False
    
    def process_all_places(self, batch_size: int = 10) -> dict:
        """
        Procesa todos los lugares y genera sus embeddings
        
        Args:
            batch_size: Número de lugares a procesar por lote
            
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
                            # Verificar si ya tiene embedding
                            if place.vector_embedding is not None:
                                logger.debug(f"Lugar {place.name} ya tiene embedding, saltando...")
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
                            
                            # Actualizar base de datos
                            if self.update_place_embedding(str(place.id), embedding):
                                stats["successful"] += 1
                                logger.info(f"✅ Procesado exitosamente: {place.name}")
                            else:
                                stats["failed"] += 1
                                logger.error(f"❌ Error actualizando BD para: {place.name}")
                            
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


def main():
    """Función principal"""
    logger.info("🚀 Iniciando generación de embeddings para lugares")
    
    # Obtener API key de OpenAI desde variable de entorno
    openai_api_key = settings.OPENAI_API_KEY
    if not openai_api_key:
        logger.error("❌ OPENAI_API_KEY no está configurada en las variables de entorno")
        return
    
    # Crear generador
    generator = PlaceEmbeddingGenerator(openai_api_key)
    
    # Procesar todos los lugares
    stats = generator.process_all_places(batch_size=10)
    
    # Mostrar resumen final
    logger.info("📊 Resumen final:")
    logger.info(f"  Total de lugares: {stats['total_places']}")
    logger.info(f"  Lugares procesados: {stats['processed']}")
    logger.info(f"  Exitosos: {stats['successful']}")
    logger.info(f"  Fallidos: {stats['failed']}")
    logger.info(f"  Saltados (ya tenían embedding): {stats['skipped']}")
    
    if stats['processed'] > 0:
        success_rate = (stats['successful'] / stats['processed']) * 100
        logger.info(f"  Tasa de éxito: {success_rate:.1f}%")
    
    if stats['successful'] > 0:
        logger.info("✅ Proceso completado exitosamente")
    else:
        logger.warning("⚠️ No se procesó ningún lugar exitosamente")


if __name__ == "__main__":
    main()
