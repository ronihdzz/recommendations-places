from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, DateTime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
import uuid
from shared.utils_dates import get_app_current_time

Base = declarative_base()


class BaseModel:
    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=get_app_current_time)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=get_app_current_time, onupdate=get_app_current_time)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }