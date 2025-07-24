# endpoints.py
from uuid import UUID
from fastapi import Request, Header, APIRouter, HTTPException, status
from shared.base_responses import EnvelopeResponse, create_response_for_fast_api
from .schema import RecommendationRequest, RecommendationResponse
from .services import get_recommendation_service
from db.qdrant.connection import qdrant_health_check

router = APIRouter(prefix="/places", tags=["Places"])


@router.get("/health/qdrant", summary="Verificar estado de Qdrant")
async def get_qdrant_health() -> dict:
    """
    Verifica el estado de la conexión con Qdrant y proporciona información de diagnóstico.
    
    Este endpoint es útil para:
    - Verificar si Qdrant está ejecutándose
    - Comprobar tiempos de respuesta
    - Ver información de colecciones disponibles
    - Diagnosticar problemas de conexión
    
    Returns:
        Información detallada del estado de Qdrant
    """
    try:
        health_status = qdrant_health_check()
        
        if health_status.get("connected", False):
            return create_response_for_fast_api(
                status_code_http=status.HTTP_200_OK,
                data=health_status,
                message="Qdrant está funcionando correctamente"
            )
        else:
            return create_response_for_fast_api(
                status_code_http=status.HTTP_503_SERVICE_UNAVAILABLE,
                data=health_status,
                message=f"Qdrant no está disponible: {health_status.get('error', 'Conexión fallida')}"
            )
            
    except Exception as e:
        error_details = {
            "connected": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
        
        return create_response_for_fast_api(
            status_code_http=status.HTTP_503_SERVICE_UNAVAILABLE,
            data=error_details,
            message=f"Error verificando estado de Qdrant: {str(e)}"
        )


@router.post("/recommendations", response_model=EnvelopeResponse, summary="Obtener recomendaciones de lugares")
async def get_place_recommendations(
    request: RecommendationRequest
) -> dict:
    """
    Obtiene recomendaciones de lugares basado en una descripción de texto.
    
    Este endpoint utiliza embeddings de OpenAI para encontrar lugares similares
    a la descripción proporcionada y devuelve los 5 más relevantes por defecto.
    
    Args:
        request: Objeto con la descripción del lugar y límite de resultados
        
    Returns:
        Respuesta con los lugares recomendados y sus scores de similitud
        
    Raises:
        HTTPException: Si ocurre un error interno del servidor
    """
    try:
        # Obtener el servicio de recomendaciones
        recommendation_service = get_recommendation_service()
        
        # Generar recomendaciones
        recommendations = await recommendation_service.get_recommendations(
            description=request.description,
            limit=request.limit
        )
        
        # Si no se encontraron recomendaciones, devolver mensaje informativo
        if recommendations.total_found == 0:
            return create_response_for_fast_api(
                status_code_http=status.HTTP_200_OK,
                data=recommendations,
                message=f"No se encontraron lugares que coincidan con la descripción: '{request.description}'"
            )
        
        # Respuesta exitosa con recomendaciones
        return create_response_for_fast_api(
            status_code_http=status.HTTP_200_OK,
            data=recommendations,
            message=f"Se encontraron {recommendations.total_found} lugares recomendados"
        )
        
    except ValueError as ve:
        # Error de configuración (ej: API key faltante)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuración: {str(ve)}"
        )
    except Exception as e:
        # Error interno del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

