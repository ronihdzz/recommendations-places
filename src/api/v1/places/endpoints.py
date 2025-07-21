# endpoints.py
from uuid import UUID
from fastapi import Request, Header, APIRouter, HTTPException, status
from shared.base_responses import EnvelopeResponse, create_response_for_fast_api
from .schema import RecommendationRequest, RecommendationResponse
from .services import get_recommendation_service

router = APIRouter(prefix="/places", tags=["Places"])


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

