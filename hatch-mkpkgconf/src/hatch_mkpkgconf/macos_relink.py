"""
    On OSX, the loader does not look at the current process to load
    dylibs -- it insists on finding them itself, so we have to fixup
    our binaries such that they resolve correctly.
    
    Two cases we need to deal with
    - Local development/installation
    - Building a wheel for pypi
    
    In development, we assume things are installed exactly where they will be
    at runtime.
      -> @loader_path/{relpath(final_location, dep_path)}
    
    For pypi wheels, we assume that installation is in site-packages, and
    so are the libraries that this lib depends on.
      -> @loader_path/{relpath(final_siterel, dep_siterel)}
    
    Notice these are the same IF you only build wheels in a virtualenv
    that only has its dependencies installed in site-packages, and that 
    there is only a single site-packages being used (so mixing --user and
    system won't work, among other things).

    This is mildly brittle, but several years of experience with it has
    shown that it's mostly not a problem.

    .. warning:: This will only work for the environment it's compiled in!
                 This basically means don't compile wheels in your development 
                 environment, use a clean environment instead

"""

# TODO: could write a standalone script that could fix rpath issues using this

import dataclasses
from os.path import basename, relpath
import pathlib
import shlex
import site
import typing as T

from delocate.delocating import filter_system_libs
from delocate.tools import get_install_names, set_install_name as _set_install_name
import pkgconf


@dataclasses.dataclass
class Library:
    #: absolute path to the package
    file_path: pathlib.Path

    #: the path relative to site-packages
    dist_path: T.Optional[pathlib.Path]


@dataclasses.dataclass
class Package:
    """Represents a package that can be found via pkgconf"""

    #: Name of the pkgconf library
    name: str

    shared_libs: T.List[Library]

    #: Other pkgconf libraries that this requires
    requires: T.Optional[T.List[str]] = None


class PackageCache:
    def __init__(self) -> None:
        self.idx: T.Dict[str, Package] = {}

    def add(self, pkg: Package):
        assert pkg.name not in self.idx
        self.idx[pkg.name] = pkg

    def get(self, name: str) -> Package:
        pkg = self.idx.get(name, None)
        if pkg is None:
            pkg = get_package(name)
            self.idx[pkg.name] = pkg
        return pkg


# def relink_libs(install_root: str, pkg: PkgCfg, pkgcfg: PkgCfgProvider):
def relink_pkgconf_packages(pkgs: T.List[Package], absolute_ok: bool):
    """
    Fix shared libraries for the given pkgconf packages

    :param pkg: Package to relink
    :param absolute_ok: If True, requirements will be set to their absolute paths.
                        This should only be used for local development, and not
                        when creating a wheel for distribution
    """

    pcache = PackageCache()
    for pkg in pkgs:
        pcache.add(pkg)

    for pkg in pkgs:
        relink_pkgconf_package(pkg, absolute_ok, pcache)


def relink_pkgconf_package(pkg: Package, absolute_ok: bool, pcache: PackageCache):
    """
    Fix shared libraries for the given pkgconf package

    :param pkg: Package to relink
    :param absolute_ok: If True, requirements will be set to their absolute paths.
                        This should only be used for local development, and not
                        when creating a wheel for distribution
    """

    if not pkg.requires:
        return

    # resolve requirements
    reqs = [pcache.get(req) for req in pkg.requires]

    if absolute_ok:
        # If we are doing an editable install, then just link to the absolute
        # path and that should be fine
        remap = {}
        for req in reqs:
            for reqlib in req.shared_libs:
                if reqlib.file_path.name in remap:
                    assert remap[reqlib.file_path.name] == str(reqlib.file_path)
                else:
                    remap[reqlib.file_path.name] = str(reqlib.file_path)

        for lib in pkg.shared_libs:
            for install_name, new_install_name in _iter_install_names(
                lib.file_path, remap
            ):
                if install_name != new_install_name:
                    set_install_name(lib.file_path, install_name, new_install_name)

    else:
        # If it's not editable, then we have to do more work to make
        # the path relative to @loader_path

        # ensure all dist paths are set correctly
        _ensure_dist_paths(reqs)

        remap = {}
        for req in reqs:
            for reqlib in req.shared_libs:
                if reqlib.file_path.name in remap:
                    assert remap[reqlib.file_path.name].file_path == reqlib.file_path
                else:
                    remap[reqlib.file_path.name] = reqlib

        for lib in pkg.shared_libs:
            assert lib.dist_path is not None
            for install_name, resolved in _iter_install_names(lib.file_path, remap):
                assert resolved.dist_path is not None
                dist_rel = relpath(str(resolved.dist_path), str(lib.dist_path.parent))
                new_install_name = f"@loader_path/{dist_rel}"

                if install_name != new_install_name:
                    set_install_name(lib.file_path, install_name, new_install_name)


def set_install_name(file: pathlib.Path, old_install_name: str, new_install_name: str):
    """Change the install name for a library

    :param file: path to a executable/library file
    :param old_install_name: current path to dependency
    :param new_install_name: new path to dependency
    """

    _set_install_name(str(file), old_install_name, new_install_name)
    print("Relink:", file, ":", old_install_name, "->", new_install_name)


def get_package(name: str) -> Package:
    """
    Queries pkgconf and returns Package information
    """

    r = pkgconf.run_pkgconf(name, "--libs-only-L", "--static", capture_output=True)
    if r.returncode != 0:
        raise ValueError(f"Could not find pkgconf package '{name}'")

    libdirs: T.List[pathlib.Path] = []
    for l in shlex.split(r.stdout.decode("utf-8").strip()):
        assert l.startswith("-L")
        libdirs.append(pathlib.Path(l[2:]))

    libs = []
    r = pkgconf.run_pkgconf(name, "--libs-only-l", "--static", capture_output=True)
    for l in shlex.split(r.stdout.decode("utf-8").strip()):
        assert l.startswith("-l")
        lname = l[2:]
        libname = f"lib{lname}.dylib"
        for ldir in libdirs:
            maybe = ldir / libname
            if maybe.exists():
                libs.append(Library(file_path=maybe, dist_path=None))
                break
        else:
            raise ValueError(f"{name}: can't locate lib '{lname}'")

    # don't need to resolve requires since --static does that for us
    return Package(name=name, shared_libs=libs, requires=[])


def _ensure_dist_paths(pkgs: T.List[Package]):

    site_packages = [pathlib.Path(pth) for pth in site.getsitepackages()]

    for pkg in pkgs:
        for lib in pkg.shared_libs:
            if lib.dist_path is not None:
                continue

            for pth in site_packages:
                if pth in lib.file_path.parents:
                    lib.dist_path = lib.file_path.relative_to(pth)
                    break
            else:
                # one of the dependencies is installed as editable or something
                # else weird, give up. Everything needs to be installed 'normally'
                raise ValueError(
                    f"pkgconf package {pkg.name} is not installed in site-packages (found at {lib.file_path})"
                )


def _iter_install_names(lib_path: pathlib.Path, remap: dict):
    for install_name in get_install_names(str(lib_path)):
        resolved = remap.get(basename(install_name))
        if resolved is None:
            if not filter_system_libs(install_name):
                continue

            raise ValueError(
                f"{lib_path}: unresolved library {install_name}: maybe a dependency is missing?"
            )

        yield install_name, resolved
