#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import List, Any, Optional, Callable
from functools import wraps
from importlib.metadata import version as getLibraryVersion

import sys

from py3nvml import py3nvml

import click
import requests

from . import ui
from ...utils.process import command


def updateLib() -> None:
    command([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--upgrade", "coretex"], ignoreStdout = True, ignoreStderr = True)


def fetchLatestVersion() -> Optional[str]:
    url = "https://pypi.org/pypi/coretex/json"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        return str(data["info"]["version"])
    else:
        return None


def checkLibVersion() -> None:
    current = getLibraryVersion("coretex")
    latest = fetchLatestVersion()

    if latest is None:
        return

    if int(current[-3:]) < int(latest[-3:]):
        ui.stdEcho(
            f"Newer version of Coretex library is available. Current: {current}, Latest: {latest}. Use \"coretex update\" command to update library to latest version."
        )

def isGPUAvailable() -> bool:
    try:
        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
        return False


def onBeforeCommandExecute(fun: Callable[..., Any], excludeOptions: Optional[List[str]] = None) -> Any:
    if excludeOptions is None:
        excludeOptions = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in excludeOptions and value:
                    return f(*args, **kwargs)

            fun()
            return f(*args, **kwargs)
        return wrapper
    return decorator
