from typing import Annotated

from fastapi import Depends, Request

from geocaching_planner.config import AppConfig


def get_settings(request: Request) -> AppConfig:
    config: AppConfig = request.app.state.config
    return config


SettingsDep = Annotated[AppConfig, Depends(get_settings)]
