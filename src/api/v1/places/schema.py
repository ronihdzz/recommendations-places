from pydantic import BaseModel, Field, ConfigDict, field_serializer
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal


class RecommendationRequest(BaseModel):
    """Schema para solicitud de recomendaciones"""
    description: str = Field(..., description="Descripción del tipo de lugar que buscas", min_length=1, max_length=500)
    limit: int = Field(default=5, description="Número de recomendaciones a obtener", ge=1, le=20)


class PlaceRecommendation(BaseModel):
    """Schema para lugar recomendado"""
    id: UUID = Field(..., description="ID único del lugar")
    name: str = Field(..., description="Nombre del lugar")
    description: Optional[str] = Field(None, description="Descripción del lugar")
    latitude: Optional[Decimal] = Field(None, description="Latitud del lugar")
    longitude: Optional[Decimal] = Field(None, description="Longitud del lugar")
    category: str = Field(..., description="Categoría del lugar")
    rating: Optional[Decimal] = Field(None, description="Calificación del lugar")
    price_level: Optional[str] = Field(None, description="Nivel de precios")
    price_average: Optional[Decimal] = Field(None, description="Precio promedio")
    price_currency: Optional[str] = Field(None, description="Moneda del precio")
    address: Optional[str] = Field(None, description="Dirección del lugar")
    similarity_score: float = Field(..., description="Score de similitud con la descripción (0.0 - 1.0)")

    @field_serializer('latitude', 'longitude', 'rating', 'price_average')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        """Convierte Decimal a float para serialización JSON"""
        return float(value) if value is not None else None

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convierte UUID a string para serialización JSON"""
        return str(value)


class RecommendationResponse(BaseModel):
    """Schema para respuesta de recomendaciones"""
    query: str = Field(..., description="Consulta original del usuario")
    total_found: int = Field(..., description="Número total de lugares encontrados")
    recommendations: list[PlaceRecommendation] = Field(..., description="Lista de lugares recomendados")

