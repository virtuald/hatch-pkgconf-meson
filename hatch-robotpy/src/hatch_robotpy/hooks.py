from hatchling.plugin import hookimpl

from .plugin import DownloadHook


@hookimpl
def hatch_register_build_hook():
    return DownloadHook
