from pydantic import BaseModel, Field, ConfigDict, field_serializer
from uuid import UUID
from datetime import datetime
from typing import Optional


class RecommendationRequest(BaseModel):
    """Schema para solicitud de recomendaciones"""
    description: str = Field(..., description="Descripción del tipo de lugar que buscas", min_length=1, max_length=500)
    limit: int = Field(default=5, description="Número de recomendaciones a obtener", ge=1, le=20)


class PlaceRecommendation(BaseModel):
    """Schema para lugar recomendado"""
    id: str = Field(..., description="ID único del lugar")
    name: str = Field(..., description="Nombre del lugar")
    category: str = Field(..., description="Categoría del lugar")
    description: Optional[str] = Field(None, description="Descripción del lugar")
    rating: Optional[float] = Field(None, description="Calificación del lugar")
    price_level: Optional[str] = Field(None, description="Nivel de precios")
    address: Optional[str] = Field(None, description="Dirección del lugar")
    similarity_score: float = Field(..., description="Porcentaje de similitud con la descripción")


class RecommendationResponse(BaseModel):
    """Schema para respuesta de recomendaciones"""
    query: str = Field(..., description="Consulta original del usuario")
    total_found: int = Field(..., description="Número total de lugares encontrados")
    recommendations: list[PlaceRecommendation] = Field(..., description="Lista de lugares recomendados")

