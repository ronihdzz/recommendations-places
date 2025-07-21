from enum import StrEnum

class AppEnvironment(StrEnum):
    LOCAL = "local", "local"
    DEVELOPMENT = "development", "dev"
    STAGING = "staging", "stg"
    PRODUCTION = "production", "prod"
    TESTING = "testing", "test"
    TESTING_DOCKER = "testing_docker", "test.docker"
    LOCAL_DOCKER = "local_docker", "local.docker"
    def __new__(cls, value: str, suffix: str) -> "AppEnvironment":
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._suffix = suffix # type: ignore
        return obj

    @property
    def suffix(self) -> str:
        return self._suffix # type: ignore
    
    @property
    def environment(self) -> str:
        return self.value

    def get_file_name(self) -> str:
        return f".env.{self.suffix}"

    @classmethod
    def _is_valid_value(cls, value: str) -> bool:
        return value in cls._value2member_map_

    @classmethod
    def _get_valid_values(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def check_value(cls, value: str) -> None:
        if not cls._is_valid_value(value):
            raise ValueError(
                f"{value} is not a valid Environment value. Valid values are: {', '.join(cls._get_valid_values())}"
            )