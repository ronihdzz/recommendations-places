from typing import ClassVar

import sentry_sdk
from loguru import logger

from core.settings.base import Settings
from shared.path import APP_ENVIRONMENT
from shared.environment import AppEnvironment
from core.settings.development import DevelopmentSettings
from core.settings.local import LocalSettings
from core.settings.production import ProductionSettings
from core.settings.staging import StagingSettings
from core.settings.testing import TestingSettings
import sys
import logging


class SettingsManager:
    
    SETTINGS_CLASS_DICT: ClassVar[dict[str, type[Settings]]] = {
        AppEnvironment.LOCAL.value: LocalSettings,
        AppEnvironment.DEVELOPMENT.value: DevelopmentSettings,
        AppEnvironment.STAGING.value: StagingSettings,
        AppEnvironment.PRODUCTION.value: ProductionSettings,
        AppEnvironment.TESTING.value: TestingSettings,
        AppEnvironment.TESTING_DOCKER.value: TestingSettings,
        AppEnvironment.LOCAL_DOCKER.value: LocalSettings,
    }

    def __init__(self, environment: str):
        self.environment = environment
        self.settings: Settings = self._get_settings()
        self._initialize_third_apps()
        self._show_project_info()

    def _initialize_third_apps(self) -> None:
        self._initialize_sentry()
        self._initialize_logger()

    def _show_project_info(self) -> None:
        logger.info(f"ENVIRONMENT: {self.settings.ENVIRONMENT}")
        logger.info(f"PROJECT: {self.settings.PROJECT.NAME}")
        logger.info(f"DESCRIPTION: {self.settings.PROJECT.DESCRIPTION}")
        logger.info(f"VERSION: {self.settings.PROJECT.VERSION}")
        logger.info(f"CODE: {self.settings.PROJECT.CODE}")
        logger.info(f"AUTHORS: {self.settings.PROJECT.AUTHORS}")
    

    def _initialize_sentry(self) -> None:
        if self.environment in [
            AppEnvironment.DEVELOPMENT,
            AppEnvironment.STAGING,
            AppEnvironment.PRODUCTION,
        ]:
            self._sentry_setup()

    def _initialize_logger(self) -> None:

        logger.remove()
        level = logging.DEBUG if self.settings.LOG.DEBUG else logging.INFO
        logger.add(
            sink=sys.stdout,
            level=level,
            colorize=self.settings.LOG.COLORIZE,
            enqueue=self.settings.LOG.ENQUEUE,
            serialize=self.settings.LOG.SERIALIZE,
        )


    def _sentry_setup(self) -> None:
        sentry_sdk.init(
            dsn=self.settings.SENTRY_DSN,
            environment=self.settings.ENVIRONMENT,
            traces_sample_rate=0,
        )

    def _get_settings(self) -> Settings:
        try:
            settings_class: type[Settings] = self.SETTINGS_CLASS_DICT[self.environment]
        except KeyError as exc:
            raise ValueError(f"Unrecognized environment value: {self.environment}") from exc
        return settings_class() # type: ignore


settings: Settings = SettingsManager(environment=APP_ENVIRONMENT).settings