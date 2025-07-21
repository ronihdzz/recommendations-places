import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from .environment import AppEnvironment

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent
logger.debug(f"BASE_DIR resolved to: {BASE_DIR}")

# Load extra paths
# ----------------------------------------------------------------
LIST_PATH_TO_ADD: list[str] = [
    # Aquí puedes añadir rutas adicionales si necesitas
]

if LIST_PATH_TO_ADD:
    sys.path.extend(LIST_PATH_TO_ADD)
    logger.info(f"Added to sys.path: {LIST_PATH_TO_ADD}")
else:
    logger.info("No extra paths to add to sys.path")


# Load base .env
# ----------------------------------------------------------------
ENVS_DIR = BASE_DIR.parent / ".envs"
logger.debug(f"ENVS_DIR resolved to: {ENVS_DIR}")

ENV_BASE_FILE_PATH = ENVS_DIR / ".env.base"
logger.info(f"Loading base environment file from: {ENV_BASE_FILE_PATH}")
if ENV_BASE_FILE_PATH.exists():
    load_dotenv(ENV_BASE_FILE_PATH)
    logger.success(f"Loaded .env.base successfully")
else:
    logger.warning(f".env.base not found at: {ENV_BASE_FILE_PATH}")


# Load environments from .env.base
# ----------------------------------------------------------------
try:
    APP_ENVIRONMENT: str = os.environ["ENVIRONMENT"]
except KeyError:
    raise ValueError("ENVIRONMENT is not set")

logger.info(f"Environment project: {APP_ENVIRONMENT}")


# Validate environments values from .env.base
# ----------------------------------------------------------------
try:
    AppEnvironment.check_value(APP_ENVIRONMENT)
    ENVIRONMENT_ENUM = AppEnvironment(APP_ENVIRONMENT) # type: ignore
    logger.success(f"Environment '{APP_ENVIRONMENT}' validated successfully")
except ValueError as e:
    logger.critical(f"Invalid ENVIRONMENT value: {APP_ENVIRONMENT} — {e}")
    raise


# Load specific env file
# ----------------------------------------------------------------
ENV_FILE_PATH = ENVS_DIR / ENVIRONMENT_ENUM.get_file_name()
logger.info(f"Loading environment-specific file from: {ENV_FILE_PATH}")

if ENV_FILE_PATH.exists():
    load_dotenv(ENV_FILE_PATH)
    logger.success(f"Loaded environment file for {APP_ENVIRONMENT} successfully")
else:
    logger.warning(f"Environment file not found: {ENV_FILE_PATH}")
