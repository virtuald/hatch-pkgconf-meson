# TODO: this came from robotpy-build, should it stay there?

from dataclasses import dataclass, field
from typing import List
import re
import sysconfig
import typing


# wpilib platforms at https://github.com/wpilibsuite/native-utils/blob/master/src/main/java/edu/wpi/first/nativeutils/WPINativeUtilsExtension.java
@dataclass
class WPILibMavenPlatform:
    arch: str

    os: str

    #: Platform tag for wheels targeted at this platform. While one could
    #: determine this programatically, that's annoying and this is easier
    tag: str

    libprefix: str = "lib"

    #: runtime linkage
    libext: str = ".so"

    #: compile time linkage
    linkext: typing.Optional[str] = None

    #: static linkage
    staticext: str = ".a"

    defines: List[str] = field(default_factory=list)

    def __post_init__(self):
        # linkext defaults to libext
        if self.linkext is None:
            self.linkext = self.libext
        self.defines = [f"{d} 1" for d in self.defines]


X86_64 = "x86-64"

# key is python platform, value is information about wpilib maven artifacts
_platforms = {
    "linux-roborio": WPILibMavenPlatform(
        arch="athena", os="linux", tag="linux_roborio", defines=["__FRC_ROBORIO__"]
    ),
    "linux-raspbian": WPILibMavenPlatform(
        arch="arm32", os="linux", tag="linux_armv7l", defines=["__RASPBIAN__"]
    ),
    "linux-armv7l": WPILibMavenPlatform(arch="arm32", os="linux", tag="linux_armv7l"),
    "linux-x86_64": WPILibMavenPlatform(
        arch=X86_64, os="linux", tag="manylinux_2_35_x86_64"
    ),
    "linux-aarch64": WPILibMavenPlatform(arch="arm64", os="linux", tag="linux_aarch64"),
    "win32": WPILibMavenPlatform(
        arch="x86",
        os="windows",
        tag="win32",
        libprefix="",
        libext=".dll",
        linkext=".lib",
        staticext=".lib",
    ),
    "win-amd64": WPILibMavenPlatform(
        arch=X86_64,
        os="windows",
        tag="win_amd64",
        libprefix="",
        libext=".dll",
        linkext=".lib",
        staticext=".lib",
    ),
    "macos-universal": WPILibMavenPlatform(
        # TODO: the wheel tag isn't correct
        arch="universal",
        os="osx",
        tag="macosx_13_0_universal2",
        libext=".dylib",
    ),
}


def get_platform_names() -> typing.List[str]:
    return list(_platforms.keys())


def get_platform(name: typing.Optional[str] = None) -> WPILibMavenPlatform:
    """
    Retrieve platform specific information
    """

    # TODO: _PYTHON_HOST_PLATFORM is used for cross builds,
    #       and is returned directly from get_platform. Might
    #       be useful to note for the future.

    if not name:
        pyplatform = sysconfig.get_platform()

        # Check for 64 bit x86 macOS (version agnostic)
        # - See https://github.com/pypa/setuptools/issues/2520 for universal2
        #   related questions? Sorta.
        if (
            re.fullmatch(r"macosx-.*-x86_64", pyplatform)
            or re.fullmatch(r"macosx-.*-arm64", pyplatform)
            or re.fullmatch(r"macosx-.*-universal2", pyplatform)
        ):
            return _platforms["macos-universal"]

        if pyplatform == "linux-armv7l":
            try:
                import distro

                distro_id = distro.id()

                if distro_id == "raspbian":
                    pyplatform = "linux-raspbian"

            except Exception:
                pass

        elif pyplatform == "linux-armv6":
            try:
                import distro

                distro_id = distro.id()

                if distro_id == "raspbian":
                    pyplatform = "linux-raspbian"
            except Exception:
                pass

        name = pyplatform

    try:
        return _platforms[name]
    except KeyError:
        raise KeyError(f"platform {name} is not supported")


def get_platform_override_keys(platform: WPILibMavenPlatform):
    # Used in places where overrides exist
    return [
        f"arch_{platform.arch}",
        f"os_{platform.os}",
        f"platform_{platform.os}_{platform.arch}",
    ]
