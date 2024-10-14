from hatchling.plugin import hookimpl

from .plugin import MkPkgconfHook


@hookimpl
def hatch_register_build_hook():
    return MkPkgconfHook
