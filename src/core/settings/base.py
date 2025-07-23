from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn, MongoDsn
from shared.path import ENV_FILE_PATH, APP_ENVIRONMENT

class ProjectSettings(BaseModel):
    NAME: str
    DESCRIPTION: str | None = None
    VERSION: str = "1.0.0"
    CODE: str
    AUTHORS: str
    LOGO_URL: str = "https://davidronihdz99.pythonanywhere.com/media/fotosPerfil/roni_3dqmEf6.jpg"

class LogSettings(BaseModel):
    DEBUG: bool = False
    COLORIZE: bool = False  
    SERIALIZE: bool = False
    ENQUEUE: bool = False

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="forbid"
    )

    # General settings
    # ----------------------------------------------------------------

    ENVIRONMENT: str = Field(
        default=APP_ENVIRONMENT,
        validate_default=True
    )
    ROOT_PATH: str | None = ""
    SENTRY_DSN: str | None = None

    TIME_ZONE: str = "America/Mexico_City"

    # Project metadata
    # ----------------------------------------------------------------

    PROJECT: ProjectSettings = Field(
        default=ProjectSettings(
            NAME="Recommendations Places",
            DESCRIPTION="Recommendations Places API",
            VERSION="1.0.0",
            CODE="001",
            AUTHORS="R2"
        ),
        validate_default=True
    )

    # Log settings
    # ----------------------------------------------------------------

    LOG: LogSettings = LogSettings(
        DEBUG=False,
        COLORIZE=False,
        SERIALIZE=False,
        ENQUEUE=False
    )

    # Database settings
    # ----------------------------------------------------------------

    # POSTGRESQL_URL: PostgresDsn
    POSTGRESQL_URL: str
    OPENAI_API_KEY: str
    # MONGO_URL: MongoDsn
    #REDIS_URL: RedisDsn
