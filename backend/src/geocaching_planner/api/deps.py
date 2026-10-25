from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from geocaching_planner.config import AppConfig


def get_settings(request: Request) -> AppConfig:
    config: AppConfig = request.app.state.config
    return config


SettingsDep = Annotated[AppConfig, Depends(get_settings)]


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
