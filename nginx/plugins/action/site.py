from __future__ import annotations
from os.path import join
from collections import namedtuple
from typing import List, Literal, Optional, Type, TypeVar, Union

from nansi.plugins.action.compose import ComposeAction
from nansi.plugins.action.args.all import Arg, ArgsBase

# pylint: disable=relative-beyond-top-level
from .config import support_role_path, CommonArgs


T = TypeVar("T")


def cast_server_names(
    value: T, expected_type: Type, **context
) -> Union[List[str], T]:
    """
    If `value` is a `str`, splits it into a list of `str`. All other `value`
    are returned as-is.

    >>> cast_server_names('example.com www.example.com')
    ['example.com', 'www.example.com']
    """
    if isinstance(value, str):
        return str.split()
    return value


class Args(ArgsBase, CommonArgs):
    # 'available' and 'disabled' are the same thing -- 'available' is the Nginx
    # term, as it ends up in the 'sites-available' directory, and 'disabled'
    # makes more sense next to 'enabled'.
    STATE_TYPE = Literal["enabled", "available", "disabled", "absent"]

    # Props
    # ========================================================================

    ### Required ###

    name = Arg(str)

    ### Optional ###

    state = Arg(STATE_TYPE, "enabled")
    server_names = Arg(
        List[str],
        lambda self, _: self.default_server_names(),
        cast=cast_server_names,
    )

    root = Arg(str, "/var/www/html")

    http = Arg(Union[bool, STATE_TYPE, Literal["redirect"]], True)
    https = Arg(Union[bool, STATE_TYPE], True)

    # http_template = Arg(str, str(support_role_path("templates/http.conf")))
    # https_template = Arg(str, str(support_role_path("templates/https.conf")))
    conf_template = Arg(str, str(support_role_path("templates/site.conf")))

    filename = Arg(str, lambda self, _: self.default_filename)
    conf_path = Arg(str, lambda self, _: self.default_conf_path)
    link_path = Arg(str, lambda self, _: self.default_link_path)

    lets_encrypt = Arg(bool, False)

    proxy = Arg(bool, False)

    proxy_location = Arg(str, "/")
    proxy_path = Arg(str, "/")
    proxy_scheme = Arg(str, "http")
    proxy_host = Arg(str, "localhost")
    proxy_port = Arg(
        Union[None, int, str], lambda self, _: self.default_proxy_port()
    )
    proxy_dest = Arg(str, lambda self, _: self.default_proxy_dest())

    client_max_body_size = Arg(str, "1m")

    @property
    def sites_available_dir(self):
        return join(self.config_dir, "sites-available")

    @property
    def sites_enabled_dir(self):
        return join(self.config_dir, "sites-enabled")

    @property
    def server_name(self) -> str:
        return " ".join(self.server_names)

    @property
    def default_filename(self) -> str:
        return f"{self.name}.conf"

    @property
    def default_conf_path(self) -> str:
        return join(self.sites_available_dir, self.filename)

    @property
    def default_link_path(self) -> str:
        return join(self.sites_enabled_dir, self.filename)

    @property
    def is_available(self) -> bool:
        return self.state != "absent"

    @property
    def is_enabled(self) -> bool:
        return self.state == "enabled"

    def default_server_names(self) -> List[str]:
        return [f"{self.name}.{self.task_vars['inventory_hostname']}"]

    def default_proxy_port(self) -> Optional[int]:
        return 8888 if self.proxy_host == "localhost" else None

    def default_proxy_dest(self) -> str:
        netloc = (
            self.proxy_host
            if self.proxy_port is None
            else f"{self.proxy_host}:{self.proxy_port}"
        )
        return f"{self.proxy_scheme}://{netloc}{self.proxy_path}"


class ActionModule(ComposeAction):
    def compose(self):
        args = Args(self._task.args, self)

        if args.is_available:
            self.tasks.template.add_vars(site=args)(
                src=self._loader.get_real_file(args.conf_template),
                dest=args.conf_path,
                # backup=True,
            )

            self.tasks.file(
                path=args.root,
                state="directory",
            )

            if args.is_enabled:
                self.tasks.file(
                    src=args.conf_path,
                    dest=args.link_path,
                    state="link",
                )
            else:
                self.tasks.file(
                    path=args.link_path,
                    state="absent",
                )
        else:
            for path in (args.link_path, args.conf_path):
                self.tasks.file(
                    path=path,
                    state="absent",
                )