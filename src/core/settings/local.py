from core.settings.base import Settings, LogSettings


class LocalSettings(Settings):

    # Log settings
    # ----------------------------------------------------------------

    LOG: LogSettings = LogSettings(
        DEBUG=False,
        COLORIZE=False,
        SERIALIZE=False,
        ENQUEUE=False
    )
