#!/usr/bin/env python3
"""
Script de diagnóstico para Qdrant
Herramienta para diagnosticar problemas de conexión y estado de Qdrant
"""

import sys
import time
import argparse
from loguru import logger
from tabulate import tabulate

from db.qdrant.connection import QdrantConnection, qdrant_health_check
from db.qdrant.repository import PlaceEmbeddingRepository
from core.settings import settings


class QdrantDiagnostic:
    """Clase para realizar diagnósticos completos de Qdrant"""
    
    def __init__(self):
        self.qdrant_conn = QdrantConnection()
        
    def check_basic_connectivity(self) -> dict:
        """Verifica conectividad básica con Qdrant"""
        logger.info("🔍 Verificando conectividad básica con Qdrant...")
        
        result = {
            "test": "Conectividad Básica",
            "status": "FAIL",
            "details": [],
            "recommendations": []
        }
        
        try:
            start_time = time.time()
            client = self.qdrant_conn.client
            response_time = time.time() - start_time
            
            result["status"] = "PASS"
            result["details"].append(f"✅ Conexión establecida en {response_time:.3f}s")
            result["details"].append(f"📍 URL: {self.qdrant_conn.url}")
            
        except ConnectionError as e:
            result["details"].append(f"❌ Error de conexión: {e}")
            result["details"].append(f"📍 URL intentada: {self.qdrant_conn.url}")
            result["recommendations"].extend([
                "Verifica que Qdrant esté ejecutándose",
                "Ejecuta: docker-compose up qdrant",
                "Revisa la configuración de QDRANT_URL en .env"
            ])
            
        except Exception as e:
            result["details"].append(f"❌ Error inesperado: {type(e).__name__}: {e}")
            result["recommendations"].append("Revisa los logs de Qdrant para más detalles")
            
        return result
    
    def check_collections(self) -> dict:
        """Verifica el estado de las colecciones"""
        logger.info("📊 Verificando estado de colecciones...")
        
        result = {
            "test": "Estado de Colecciones",
            "status": "FAIL",
            "details": [],
            "recommendations": []
        }
        
        try:
            collections = self.qdrant_conn.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            result["status"] = "PASS"
            result["details"].append(f"📈 Total de colecciones: {len(collection_names)}")
            
            if collection_names:
                result["details"].append(f"📋 Colecciones existentes:")
                for name in collection_names:
                    result["details"].append(f"   - {name}")
            else:
                result["details"].append("⚠️ No hay colecciones creadas")
                result["recommendations"].append("Ejecuta el script de creación de embeddings")
                
            # Verificar colección específica de places
            expected_collection = settings.QDRANT_COLLECTION_NAME
            if expected_collection in collection_names:
                result["details"].append(f"✅ Colección '{expected_collection}' encontrada")
                
                # Obtener información detallada
                try:
                    collection_info = self.qdrant_conn.client.get_collection(expected_collection)
                    result["details"].append(f"📊 Puntos en colección: {collection_info.points_count}")
                    result["details"].append(f"🗄️ Segmentos: {collection_info.segments_count}")
                    
                    if collection_info.points_count == 0:
                        result["recommendations"].append("La colección está vacía, ejecuta el script de embeddings")
                        
                except Exception as detail_error:
                    result["details"].append(f"⚠️ Error obteniendo detalles: {detail_error}")
                    
            else:
                result["details"].append(f"❌ Colección '{expected_collection}' no encontrada")
                result["recommendations"].extend([
                    f"Crea la colección '{expected_collection}'",
                    "Ejecuta: python src/create_embedings_qdrant.py"
                ])
                
        except Exception as e:
            result["details"].append(f"❌ Error consultando colecciones: {e}")
            result["recommendations"].append("Verifica que Qdrant esté funcionando correctamente")
            
        return result
    
    def check_performance(self) -> dict:
        """Verifica el rendimiento de Qdrant"""
        logger.info("⚡ Verificando rendimiento de Qdrant...")
        
        result = {
            "test": "Rendimiento",
            "status": "FAIL",
            "details": [],
            "recommendations": []
        }
        
        try:
            # Test de múltiples operaciones para medir rendimiento
            operations = []
            
            # Test 1: Obtener colecciones (múltiples veces)
            times = []
            for i in range(5):
                start = time.time()
                self.qdrant_conn.client.get_collections()
                times.append(time.time() - start)
                
            avg_time = sum(times) / len(times)
            operations.append(("get_collections", avg_time))
            
            # Test 2: Obtener info de colección específica
            try:
                start = time.time()
                self.qdrant_conn.client.get_collection(settings.QDRANT_COLLECTION_NAME)
                collection_time = time.time() - start
                operations.append(("get_collection_info", collection_time))
            except:
                operations.append(("get_collection_info", "N/A (colección no existe)"))
            
            result["status"] = "PASS"
            result["details"].append("📊 Tiempos de respuesta promedio:")
            
            for operation, time_taken in operations:
                if isinstance(time_taken, float):
                    status = "🟢" if time_taken < 0.1 else "🟡" if time_taken < 0.5 else "🔴"
                    result["details"].append(f"   {status} {operation}: {time_taken:.3f}s")
                    
                    if time_taken > 1.0:
                        result["recommendations"].append(f"Rendimiento lento en {operation}")
                else:
                    result["details"].append(f"   ⚠️ {operation}: {time_taken}")
                    
        except Exception as e:
            result["details"].append(f"❌ Error en test de rendimiento: {e}")
            
        return result
    
    def check_configuration(self) -> dict:
        """Verifica la configuración actual"""
        logger.info("🔧 Verificando configuración...")
        
        result = {
            "test": "Configuración",
            "status": "PASS",
            "details": [],
            "recommendations": []
        }
        
        # Configuración de URL
        result["details"].append(f"📍 QDRANT_URL: {settings.QDRANT_URL}")
        
        # API Key
        if settings.QDRANT_API_KEY:
            result["details"].append(f"🔑 API Key: Configurada ({len(settings.QDRANT_API_KEY)} caracteres)")
        else:
            result["details"].append("🔑 API Key: No configurada")
            
        # Nombre de colección
        result["details"].append(f"📊 Colección: {settings.QDRANT_COLLECTION_NAME}")
        
        # Validar URL
        if not settings.QDRANT_URL.startswith(('http://', 'https://')):
            result["status"] = "FAIL"
            result["details"].append("❌ URL de Qdrant no válida")
            result["recommendations"].append("Configura QDRANT_URL con formato http:// o https://")
            
        return result
    
    def run_full_diagnostic(self) -> list:
        """Ejecuta diagnóstico completo"""
        logger.info("🚀 Iniciando diagnóstico completo de Qdrant...")
        
        tests = [
            self.check_configuration,
            self.check_basic_connectivity,
            self.check_collections,
            self.check_performance
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                
                # Log inmediato del resultado
                status_icon = "✅" if result["status"] == "PASS" else "❌"
                logger.info(f"{status_icon} {result['test']}: {result['status']}")
                
            except Exception as e:
                logger.error(f"❌ Error ejecutando test {test.__name__}: {e}")
                results.append({
                    "test": test.__name__,
                    "status": "ERROR",
                    "details": [f"Error ejecutando test: {e}"],
                    "recommendations": ["Revisa los logs para más detalles"]
                })
                
        return results


def print_diagnostic_report(results: list):
    """Imprime reporte de diagnóstico formateado"""
    print("\n" + "="*80)
    print("📋 REPORTE DE DIAGNÓSTICO DE QDRANT")
    print("="*80)
    
    # Resumen
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    
    summary_table = [
        ["Total de tests", total],
        ["Exitosos", passed],
        ["Fallidos", total - passed],
        ["Estado general", "✅ SALUDABLE" if passed == total else "❌ REQUIERE ATENCIÓN"]
    ]
    
    print("\n📊 RESUMEN:")
    print(tabulate(summary_table, headers=["Métrica", "Valor"], tablefmt="grid"))
    
    # Detalles por test
    print("\n🔍 DETALLES POR TEST:")
    for result in results:
        status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
        print(f"\n{status_icon} {result['test'].upper()} - {result['status']}")
        print("-" * 50)
        
        if result["details"]:
            for detail in result["details"]:
                print(f"  {detail}")
                
        if result["recommendations"]:
            print(f"\n  💡 RECOMENDACIONES:")
            for rec in result["recommendations"]:
                print(f"     • {rec}")
    
    # Recomendaciones generales
    all_recommendations = []
    for result in results:
        all_recommendations.extend(result["recommendations"])
        
    if all_recommendations:
        print(f"\n🛠️ RECOMENDACIONES GENERALES:")
        print("-" * 50)
        for i, rec in enumerate(set(all_recommendations), 1):
            print(f"{i}. {rec}")
    
    print("\n" + "="*80)


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Diagnóstico de Qdrant")
    parser.add_argument("--verbose", "-v", action="store_true", help="Salida detallada")
    parser.add_argument("--quick", "-q", action="store_true", help="Solo verificación básica")
    
    args = parser.parse_args()
    
    # Configurar logger
    logger.remove()
    level = "DEBUG" if args.verbose else "INFO"
    logger.add(sys.stdout, format="<level>{level}</level> | {message}", level=level)
    
    # Crear instancia de diagnóstico
    diagnostic = QdrantDiagnostic()
    
    try:
        if args.quick:
            # Solo conectividad básica
            logger.info("🚀 Ejecutando verificación rápida...")
            results = [diagnostic.check_basic_connectivity()]
        else:
            # Diagnóstico completo
            results = diagnostic.run_full_diagnostic()
            
        # Imprimir reporte
        print_diagnostic_report(results)
        
        # Código de salida
        failed_tests = sum(1 for r in results if r["status"] in ["FAIL", "ERROR"])
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Diagnóstico interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error ejecutando diagnóstico: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 