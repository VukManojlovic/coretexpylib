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

from typing import Final
from typing_extensions import Self
from datetime import datetime

import sys
import logging
import multiprocessing
import faulthandler
import signal

from ._experiment_worker import experimentWorker
from ._current_experiment import setCurrentExperiment
from .. import folder_manager
from ..coretex import Experiment
from ..logging import LogHandler
from ..utils import DATE_FORMAT


class TaskCallback:

    def __init__(self, experiment: Experiment, refreshToken: str) -> None:
        self._experiment: Final = experiment

        self.__outputStream, self.__inputStream = multiprocessing.Pipe()

        self.workerProcess = multiprocessing.Process(
            name = f"Experiment {experiment.id} worker process",
            target = experimentWorker,
            args = (self.__outputStream, refreshToken, self._experiment.id),
            daemon = True
        )

    @classmethod
    def create(cls, experimentId: int, refreshToken: str) -> Self:
        return cls(Experiment.fetchById(experimentId), refreshToken)

    def onStart(self) -> None:
        self.workerProcess.start()

        result = self.__inputStream.recv()
        if result["code"] != 0:
            raise RuntimeError(result["message"])

        logging.getLogger("coretexpylib").info(result["message"])

        # Call "kill -30 experiment_process_id" to dump current stack trace of the experiment into the file
        # 30 == signal.SIGUSR1
        # Only works on *nix systems
        faultHandlerPath = folder_manager.logs / f"experiment_stacktrace_{self._experiment.id}_{datetime.now().strftime(DATE_FORMAT)}.log"
        faulthandler.register(
            signal.SIGUSR1,
            file = faultHandlerPath.open("w"),
            all_threads = True
        )

    def onSuccess(self) -> None:
        logging.getLogger("coretexpylib").info("Experiment finished successfully")

        LogHandler.instance().flushLogs()
        LogHandler.instance().reset()

    def onKeyboardInterrupt(self) -> None:
        pass

    def onException(self, exception: BaseException) -> None:
        logging.getLogger("coretexpylib").critical("Experiment failed to finish due to an error")
        logging.getLogger("coretexpylib").debug(exception, exc_info = True)
        logging.getLogger("coretexpylib").critical(str(exception))

        LogHandler.instance().flushLogs()
        LogHandler.instance().reset()

    def onNetworkConnectionLost(self) -> None:
        folder_manager.clearTempFiles()

        sys.exit(1)

    def onCleanUp(self) -> None:
        self.workerProcess.kill()
        self.workerProcess.join()

        try:
            from py3nvml import py3nvml
            py3nvml.nvmlShutdown()
        except:
            pass

        folder_manager.clearTempFiles()
        setCurrentExperiment(None)