from db.mongo import BaseMongoDocument
from .constants import BookType

class BookDocument(BaseMongoDocument):
    title: str
    author: str
    year: int
    type: BookType