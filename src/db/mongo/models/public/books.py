from db.mongo.base import MongoAbstractRepository

from .schemas import (
    BookDocument,
)


class BookMongoRepository(MongoAbstractRepository):
    collection_name = "books"
    document_model = BookDocument

