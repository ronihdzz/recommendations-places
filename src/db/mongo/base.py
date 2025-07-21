import uuid
from abc import ABC
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_serializer

from shared.utils_dates import get_app_current_time

from .connection import MongoDBConnection


def default_mongodb_id():
    return uuid.uuid4()


def default_mongodb_created_at():
    return get_app_current_time()


class BaseMongoDocument(BaseModel):
    id: UUID = Field(default_factory=default_mongodb_id, alias="_id")
    created_at: datetime = Field(default_factory=default_mongodb_created_at)
    updated_at: datetime = Field(default_factory=default_mongodb_created_at)
    deleted_at: datetime | None = Field(default=None)


    model_config = ConfigDict(validate_by_name=False)

    @field_serializer('id')
    def serialize_id(self, v: UUID, _info):
        return str(v)


class MongoAbstractRepository(ABC):
    collection_name: str
    document_model: type[BaseMongoDocument]

    def __init__(self):
        self._validate_attributes()
        self._init_collection()

    def _init_collection(self):
        self.collection = MongoDBConnection.get_collection(self.collection_name)

    def _validate_attributes(self):
        if not self.collection_name:
            raise ValueError("Collection name is required")
        if not self.document_model:
            raise ValueError("Document model is required")

    def add(self, data: BaseMongoDocument) -> BaseMongoDocument:
        if not isinstance(data, self.document_model):
            raise TypeError(f"Expected {self.document_model}, got {type(data)}")
        self.collection.insert_one(data.model_dump(mode="json"))
