from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from core.settings import settings
from db.posgresql.base import Base
from db.posgresql.models.public import Place, PlaceCategory, PriceLevel
from loguru import logger


def extract_schemas_from_models(models: list) -> set[str]:
    """Extract unique schema names from SQLAlchemy models"""
    schemas = set()
    for model in models:
        table_args = getattr(model, '__table_args__', None)
        if table_args and isinstance(table_args, dict):
            schema = table_args.get('schema')
            if schema:
                schemas.add(schema)
        # Also check if schema is defined directly in __table__
        elif hasattr(model, '__table__') and hasattr(model.__table__, 'schema'):
            schema = model.__table__.schema
            if schema:
                schemas.add(schema)
    
    # Always include 'public' schema as it's the default
    schemas.add('public')
    return schemas


def create_schema(engine, schema_name):
    """Create a schema if it doesn't exist"""
    from sqlalchemy import text
    schema_format = "CREATE SCHEMA IF NOT EXISTS {}"
    query_schema = text(schema_format.format(schema_name))
    with engine.connect() as conn, conn.begin():
        logger.info(f"Creating schema: {schema_name}")
        conn.execute(query_schema)


def create_schemas(engine, schemas_to_create: list[str]):
    """Create multiple schemas"""
    for schema in schemas_to_create:
        create_schema(engine, schema)


def create_specific_tables(engine, tables: list):
    for table in tables:
        logger.info(f"Creating table: {table.name}")
        table.create(engine, checkfirst=True)  # checkfirst=True solo crea si no existe


def prepare_specific_tables(models: list, schemas_to_create: list[str]):
    logger.info(f"Creating tables")
    engine = create_engine(
        settings.POSTGRESQL_URL.unicode_string(),
        poolclass=NullPool,
        echo=True  # <-- ¡Activa logs!
    )
    logger.info(f"Engine created")
    
    # Create specified schemas first
    logger.info(f"Creating schemas: {schemas_to_create}")
    create_schemas(engine, schemas_to_create)
    logger.info(f"Schemas created")
    
    # Create tables
    tables = [model.__table__ for model in models]
    create_specific_tables(engine, tables)
    logger.info(f"Tables created")

if __name__ == "__main__":
    logger.info(f"Creating tables")
    
    # Definir esquemas a crear
    schemas_to_create = [
        "public",
    ]
    
    # Definir modelos/tablas a crear
    models_to_create = [
        Place,
    ]
    
    prepare_specific_tables(
        models=models_to_create,
        schemas_to_create=schemas_to_create
    )
