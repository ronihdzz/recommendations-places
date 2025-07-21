import certifi
from pymongo import MongoClient

from core.settings import settings
from shared.environment import Environment


class MongoDBConnection:
    _client = None
    _db = None

    @staticmethod
    def get_db(mongo_url=None, force_update=False):  # noqa: FBT002
        """
        Returns the single instance of the database.
        Parameters:
          - mongo_url: Connection URL including the database.
          - force_update: If True, forces the creation of a new connection.
        """

        if mongo_url is None:
            # mongo_url = settings.MONGO_URL.unicode_string()
            mongo_url = settings.MONGO_URL
        if MongoDBConnection._db is None or force_update:
            # Create MongoDB client
            MongoDBConnection._client = MongoDBConnection.get_mongo_client(mongo_url)
            # Get the database from the URL
            MongoDBConnection._db = MongoDBConnection._client.get_database()
        return MongoDBConnection._db

    @staticmethod
    def get_collection(collection_name: str):
        db = MongoDBConnection.get_db()
        return db[collection_name]

    @staticmethod
    def get_mongo_client(mongo_url: str):
        if settings.ENVIRONMENT != Environment.LOCAL:
            ca = certifi.where()
            client = MongoClient(mongo_url, tlsCAFile=ca)
        else:
            client = MongoClient(mongo_url)
        return client
