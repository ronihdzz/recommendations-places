import os
import requests
from core.settings import settings


QDRANT_URL = settings.QDRANT_URL
QDRANT_API_KEY = settings.QDRANT_API_KEY

HEADERS = {
    "Content-Type": "application/json",
    "api-key": QDRANT_API_KEY
}


def check_health():
    resp = requests.get(f"{QDRANT_URL}/healthz")
    print("✅ /healthz:", resp.status_code, resp.text)


def list_collections():
    resp = requests.get(f"{QDRANT_URL}/collections", headers=HEADERS)
    print("📚 Collections:", resp.status_code, resp.json())


def create_collection(name: str, vector_size: int = 3):
    payload = {
        "vectors": {
            "size": vector_size,
            "distance": "Cosine"
        }
    }
    resp = requests.put(f"{QDRANT_URL}/collections/{name}", headers=HEADERS, json=payload)
    print(f"🆕 Create '{name}':", resp.status_code, resp.text)


def insert_points(collection_name: str):
    payload = {
        "points": [
            {
                "id": 1,
                "vector": [0.1, 0.2, 0.3],
                "payload": {"nombre": "Lugar 1"}
            },
            {
                "id": 2,
                "vector": [0.4, 0.5, 0.6],
                "payload": {"nombre": "Lugar 2"}
            }
        ]
    }
    resp = requests.put(f"{QDRANT_URL}/collections/{collection_name}/points", headers=HEADERS, json=payload)
    print("📌 Insert points:", resp.status_code, resp.text)


def search_vectors(collection_name: str):
    payload = {
        "vector": [0.1, 0.2, 0.3],
        "top": 2
    }
    resp = requests.post(f"{QDRANT_URL}/collections/{collection_name}/points/search", headers=HEADERS, json=payload)
    print("🔍 Search:", resp.status_code)
    print(resp.json())


if __name__ == "__main__":
    check_health()
    list_collections()

    COLLECTION = "lugares_demo"
    create_collection(COLLECTION)
    insert_points(COLLECTION)
    search_vectors(COLLECTION)
