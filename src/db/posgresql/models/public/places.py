from sqlalchemy import Column, String, Float, Time, Numeric, Text
from sqlalchemy.orm import relationship
from db.posgresql.base import Base, BaseModel
from sqlalchemy.dialects.postgresql import UUID
from .constants import PlaceCategory, PriceLevel


class Place(Base, BaseModel):
    __tablename__ = "places"
    __table_args__ = {"schema": "public"}

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Numeric(precision=10, scale=7), nullable=False)
    longitude = Column(Numeric(precision=10, scale=7), nullable=False)
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    category = Column(String(50), nullable=False)  # PlaceCategory enum
    rating = Column(Numeric(precision=3, scale=2), nullable=True)
    price_level = Column(String(10), nullable=True)  # PriceLevel enum
    price_average = Column(Numeric(precision=10, scale=2), nullable=True)
    price_currency = Column(String(10), nullable=True, default="MXN")
    address = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Place(name='{self.name}', category='{self.category}', rating={self.rating})>"
    
    def to_dict(self):
        result = super().to_dict()
        # Convert time objects to string for JSON serialization
        if result.get('open_time'):
            result['open_time'] = str(result['open_time'])
        if result.get('close_time'):
            result['close_time'] = str(result['close_time'])
        # Convert Decimal to float for JSON serialization
        if result.get('latitude'):
            result['latitude'] = float(result['latitude'])
        if result.get('longitude'):
            result['longitude'] = float(result['longitude'])
        if result.get('rating'):
            result['rating'] = float(result['rating'])
        if result.get('price_average'):
            result['price_average'] = float(result['price_average'])
        return result 