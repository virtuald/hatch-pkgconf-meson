import dataclasses
import pathlib
import typing as T


@dataclasses.dataclass
class PcFileConfig:
    """
    Contents of [[tool.hatch.build.hooks.mkpkgconf.pcfile]] items
    """

    # TODO: support platform-specific generation
    #   tool.hatch.build.hooks.mkpkgconf.windows.pcfile, etc

    outpath: str
    """
    Output directory to write the NAME.pc and INITPY.py file to (relative
    to pyproject.toml)
    """

    name: str
    """Name of the .pc file and the package name"""

    description: str
    """Description of this package"""

    version: T.Optional[str] = None
    """If not specified, set to package version"""

    includedir: T.Optional[str] = None
    """Where include files can be found (relative to pyproject.toml)"""

    libdir: T.Optional[str] = None
    """Where the library is located. If not specified, it is in outpath"""

    shared_libraries: T.Optional[T.List[str]] = None
    """Name of shared libraries located in libdir (without extension)"""

    libs_private: T.Optional[str] = None
    """The link flags for private libraries not exposed to applications"""

    requires: T.Optional[T.List[str]] = None
    """
    Names of other packages this package requires. They must be installed
    at build time.
    """

    requires_private: T.Optional[T.List[str]] = None
    """
    Names of private packages this package requires. They must be installed
    at build time.
    """

    extra_cflags: T.Optional[str] = None
    """A list of extra compiler flags to be added to Cflags after header search path"""

    extra_link_flags: T.Optional[str] = None
    """A list of extra link flags to be added to Libs"""

    variables: T.Optional[T.Dict[str, str]] = None
    """
    Custom variables to add to the generated file. Prefix, libdir, includedir must not be specified."""

    init_module: str = "auto"
    """
    If specified, the name of the python module that will be written next to
    the .pc file which will load the shared_libraries
    """

    def get_out_path(self) -> pathlib.Path:
        outpath = pathlib.PurePosixPath(self.outpath)
        if outpath.is_absolute():
            raise ValueError(f"outpath must not be absolute ({outpath})")
        return pathlib.Path(outpath)

    def get_pc_path(self) -> pathlib.Path:
        return self.get_out_path() / f"{self.name}.pc"

    def get_init_module(self) -> str:
        if self.init_module == "auto":
            module = f"_init_{self.name}"
        else:
            module = self.init_module

        if not module.isidentifier():
            raise ValueError(
                f"init_module must be a valid python identifier (got {module})"
            )
        return module

    def get_init_module_path(self) -> pathlib.Path:
        module = self.get_init_module()
        return self.get_out_path() / f"{module}.py"
