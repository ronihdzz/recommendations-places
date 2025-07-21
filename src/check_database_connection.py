from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from loguru import logger
from db.posgresql.connection import get_db_context
from sqlalchemy import text

# Define aquí tu URL de conexión a PostgreSQL
POSTGRESQL_URL = "postgresql://roni:roni123@localhost:9999/places"


def test_connection(url: str) -> bool:
    """Test PostgreSQL connection"""
    try:
        with get_db_context() as session:
            session.execute(text("SELECT 1"))
        logger.info("¡Conexión a la base de datos exitosa!")
        return True
    except Exception as e:
        logger.error(f"Fallo la conexión a la base de datos: {str(e)}")
        return False


if __name__ == "__main__":
    logger.info("Probando conexión a PostgreSQL...")
    if test_connection(POSTGRESQL_URL):
        print("Conexión exitosa ✅")
    else:
        print("Conexión fallida ❌")
