from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from db.posgresql.models.public.places import Place
from db.posgresql.models.public.constants import PlaceCategory


class PlaceRepository:
    """Repository for Place operations using SQLAlchemy"""
    
    def __init__(self, session: Session):
        self.session = session

    def add(self, place: Place) -> Place:
        """Add a new place to the database"""
        self.session.add(place)
        self.session.commit()
        self.session.refresh(place)
        return place

    def get_by_id(self, place_id: UUID) -> Optional[Place]:
        """Get a place by its ID"""
        return self.session.query(Place).filter(
            and_(Place.id == place_id, Place.deleted_at.is_(None))
        ).first()

    def get_places_by_ids(self, place_ids: List[str]) -> List[Place]:
        """Get multiple places by their IDs"""
        # Convertir string IDs a UUID objects
        uuid_ids = []
        for place_id in place_ids:
            try:
                if isinstance(place_id, str):
                    uuid_ids.append(UUID(place_id))
                else:
                    uuid_ids.append(place_id)
            except ValueError:
                # Skip invalid UUIDs
                continue
        
        if not uuid_ids:
            return []
            
        return self.session.query(Place).filter(
            and_(Place.id.in_(uuid_ids), Place.deleted_at.is_(None))
        ).all()

    def get_by_name(self, name: str) -> Optional[Place]:
        """Get a place by its name"""
        return self.session.query(Place).filter(
            and_(Place.name == name, Place.deleted_at.is_(None))
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Place]:
        """Get all places with pagination"""
        return self.session.query(Place).filter(
            Place.deleted_at.is_(None)
        ).offset(skip).limit(limit).all()

    def get_by_category(self, category: PlaceCategory, skip: int = 0, limit: int = 100) -> List[Place]:
        """Get places by category"""
        return self.session.query(Place).filter(
            and_(Place.category == category, Place.deleted_at.is_(None))
        ).offset(skip).limit(limit).all()

    def get_by_location(self, latitude: float, longitude: float, radius_km: float = 1.0) -> List[Place]:
        """Get places within a radius from a given location (simplified distance calculation)"""
        lat_delta = radius_km / 111.0  # Approximate degrees per km
        lng_delta = radius_km / (111.0 * abs(latitude))  # Adjusted for latitude
        
        return self.session.query(Place).filter(
            and_(
                Place.latitude.between(latitude - lat_delta, latitude + lat_delta),
                Place.longitude.between(longitude - lng_delta, longitude + lng_delta),
                Place.deleted_at.is_(None)
            )
        ).all()

    def search_by_name_or_description(self, query: str, skip: int = 0, limit: int = 50) -> List[Place]:
        """Search places by name or description"""
        search_term = f"%{query}%"
        return self.session.query(Place).filter(
            and_(
                or_(
                    Place.name.ilike(search_term),
                    Place.description.ilike(search_term)
                ),
                Place.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()

    def update(self, place: Place) -> Place:
        """Update a place"""
        self.session.commit()
        self.session.refresh(place)
        return place

    def delete(self, place_id: UUID) -> bool:
        """Soft delete a place"""
        place = self.get_by_id(place_id)
        if place:
            from shared.utils_dates import get_app_current_time
            place.deleted_at = get_app_current_time()
            self.session.commit()
            return True
        return False

    def count(self) -> int:
        """Count total active places"""
        return self.session.query(Place).filter(Place.deleted_at.is_(None)).count()

    def count_by_category(self, category: PlaceCategory) -> int:
        """Count places by category"""
        return self.session.query(Place).filter(
            and_(Place.category == category, Place.deleted_at.is_(None))
        ).count() 