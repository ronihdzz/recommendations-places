#!/usr/bin/env python3
"""
Script para verificar la conexión con Qdrant y realizar pruebas básicas
"""

import sys
import uuid
from typing import List
from loguru import logger
from db.qdrant.connection import QdrantConnection, get_qdrant_client
from db.qdrant.repository import PlaceEmbeddingRepository


def test_qdrant_connection():
    """Prueba la conexión básica con Qdrant"""
    logger.info("🔍 Verificando conexión con Qdrant...")
    
    try:
        # Crear conexión
        qdrant_conn = QdrantConnection()
        
        # Verificar conexión
        if qdrant_conn.is_connected():
            logger.success("✅ Conexión con Qdrant establecida exitosamente")
            return True
        else:
            logger.error("❌ No se pudo establecer conexión con Qdrant")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error al conectar con Qdrant: {e}")
        return False


def test_collection_operations():
    """Prueba las operaciones básicas de colecciones"""
    logger.info("🗂️  Probando operaciones de colecciones...")
    
    try:
        client = get_qdrant_client()
        
        # Listar colecciones
        collections = client.get_collections()
        logger.info(f"📊 Colecciones existentes: {[col.name for col in collections.collections]}")
        
        # Crear repositorio de prueba
        test_repo = PlaceEmbeddingRepository("test_collection")
        
        # Crear colección de prueba
        test_repo.create_collection()
        logger.success("✅ Colección de prueba creada exitosamente")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en operaciones de colección: {e}")
        return False


def test_embedding_operations():
    """Prueba las operaciones básicas de embeddings"""
    logger.info("🧮 Probando operaciones de embeddings...")
    
    try:
        # Crear repositorio de prueba
        test_repo = PlaceEmbeddingRepository("test_collection")
        
        # Datos de prueba
        test_embedding = [0.1] * 1536  # Vector de prueba con dimensiones correctas
        test_place_id = str(uuid.uuid4())  # Generar UUID válido
        test_metadata = {
            "name": "Restaurante de Prueba",
            "category": "restaurant",
            "rating": 4.5,
            "address": "Calle Ficticia 123"
        }
        
        # Insertar embedding de prueba
        test_repo.upsert_embedding(test_place_id, test_embedding, test_metadata)
        logger.success("✅ Embedding de prueba insertado exitosamente")
        
        # Buscar lugares similares
        similar_places = test_repo.search_similar_places(
            query_embedding=test_embedding,
            limit=5,
            score_threshold=0.5
        )
        
        logger.info(f"🔍 Lugares similares encontrados: {len(similar_places)}")
        if similar_places:
            for place in similar_places:
                logger.info(f"   - ID: {place['place_id']}, Score: {place['score']:.3f}")
        
        # Obtener información de la colección
        collection_info = test_repo.get_collection_info()
        logger.info(f"📈 Información de la colección: {collection_info}")
        
        # Limpiar el embedding de prueba
        test_repo.delete_embedding(test_place_id)
        logger.info(f"🧹 Embedding de prueba eliminado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en operaciones de embedding: {e}")
        return False


def cleanup_test_data():
    """Limpia los datos de prueba"""
    logger.info("🧹 Limpiando datos de prueba...")
    
    try:
        client = get_qdrant_client()
        
        # Eliminar colección de prueba
        try:
            client.delete_collection("test_collection")
            logger.success("✅ Colección de prueba eliminada")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo eliminar la colección de prueba: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        return False


def main():
    """Función principal del script"""
    logger.info("🚀 Iniciando verificación de Qdrant...")
    
    # Configurar logger
    logger.remove()
    logger.add(sys.stdout, format="<level>{level}</level> | {message}", level="INFO")
    
    tests_passed = 0
    total_tests = 4
    
    # Ejecutar pruebas
    tests = [
        ("Conexión básica", test_qdrant_connection),
        ("Operaciones de colección", test_collection_operations),
        ("Operaciones de embedding", test_embedding_operations),
        ("Limpieza", cleanup_test_data)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Ejecutando: {test_name}")
        logger.info(f"{'='*50}")
        
        if test_func():
            tests_passed += 1
        
    # Mostrar resultados finales
    logger.info(f"\n{'='*50}")
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info(f"{'='*50}")
    logger.info(f"Pruebas pasadas: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        logger.success("🎉 ¡Todas las pruebas pasaron exitosamente!")
        logger.success("✅ Qdrant está configurado correctamente y listo para usar")
        return 0
    else:
        logger.error(f"❌ {total_tests - tests_passed} prueba(s) fallaron")
        logger.error("🔧 Verifica la configuración de Qdrant")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 