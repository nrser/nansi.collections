# pylint: disable=logging-too-many-args

from __future__ import annotations
from typing import *
import logging
from os.path import basename, isabs, join
from collections import abc

from nansi.plugins.action.compose import ComposeAction
from nansi.plugins.action.args import (
    Arg,
    ArgsBase,
)
from nansi.utils.strings import connect
from nansi.support.systemd import file_content_for

LOG = logging.getLogger(__name__)

class SystemdUnit(ArgsBase):
    file_dir = Arg(str, "/etc/systemd/system")
    state = Arg(Literal["present", "absent"], "present")
    name = Arg(str)
    data = Arg(Dict[str, Any])
    mode = Arg(Union[str, int], 0o600)

    @property
    def filename(self) -> str:
        return f"{self.name}.service"

    @property
    def file_content(self) -> str:
        return file_content_for(self.data)

    @property
    def file_path(self) -> str:
        return connect(self.file_dir, self.filename)

    @property
    def config_dir(self) -> str:
        return connect(self.configs_dir, self.name)


class ActionModule(ComposeAction):
    def append_result(self, task, action, result):
        if "results" not in self._result:
            self._result["results"] = []
        self._result["results"].append(
            {
                "task": task.action,
                "args": task.args,
                "status": self.result_status(result),
            }
        )

    def state_present(self, unit: SystemdUnit):
        unit_file = self.tasks.copy(
            dest=unit.file_path,
            content=unit.file_content,
            mode=unit.mode,
        )

        self.tasks.systemd(
            name=unit.filename,
            state=(
                "restarted" if self._result.get("changed", False) else "started"
            ),
            enabled=True,
            daemon_reload=unit_file.get("changed", False),
        )

    def state_absent(self, unit: SystemdUnit):
        self.tasks.systemd(
            name=unit.filename,
            state="stopped",
            enabled=False,
        )
        self.tasks.file(path=unit.file_path, state="absent")

    def compose(self):
        service = SystemdUnit(self._task.args, self._task_vars)
        getattr(self, f"state_{service.state}")(service)