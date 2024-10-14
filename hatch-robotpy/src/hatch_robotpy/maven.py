import typing as T

from .config import Download, MavenLibDownload


def _get_artifact_url(dlcfg: MavenLibDownload, classifier: str) -> str:
    # TODO: support development against locally installed things?
    repo_url = dlcfg.repo_url
    grp = dlcfg.group_id.replace(".", "/")
    art = dlcfg.artifact_id
    ver = dlcfg.version

    return f"{repo_url}/{grp}/{art}/{ver}/{art}-{ver}-{classifier}.zip"


def convert_maven_to_downloads(mcfg: MavenLibDownload) -> T.List[Download]:
    """
    Converts a MavenLibDownload object to a list of normal downloads
    """

    dl_lib = {}
    dl_static = {}
    dl_header = {}
    dl_sources = {}

    # if mcfg.use_sources:
    #     if static:
    #         raise ValueError("Cannot specify sources in static_lib section")

    #     # sources don't have libs, ignore them
    #     dl_sources["url"] = _get_artifact_url(mcfg, mcfg.sources_classifier)
    #     dl_sources["sources"] = mcfg.sources
    #     dl_sources["patches"] = mcfg.patches
    # elif mcfg.sources is not None:
    #     raise ValueError("sources must be None if use_sources is False!")
    # elif mcfg.patches is not None:
    #     raise ValueError("patches must be None if use_sources is False!")
    # else:
    if True:
        # libs

        libs = mcfg.libs
        if mcfg.staticlibs is None and libs is None:
            libs = [mcfg.artifact_id]

        if libs is not None:
            dl_lib["extract_to"] = mcfg.extract_to
            dl_lib["libs"] = libs
            dl_lib["libdir"] = "${OS}/${ARCH}/shared"
            dl_lib["url"] = _get_artifact_url(mcfg, "${OS}${ARCH}")
            dl_lib["strip"] = mcfg.strip

        if mcfg.staticlibs is not None:
            dl_static["extract_to"] = mcfg.extract_to
            dl_static["staticlibs"] = mcfg.staticlibs
            dl_static["libdir"] = "${OS}/${ARCH}/static"
            dl_static["url"] = _get_artifact_url(mcfg, "${OS}${ARCH}static")
            dl_static["strip"] = mcfg.strip

    # headers
    dl_header["extract_to"] = mcfg.extract_to
    dl_header["incdir"] = ""
    dl_header["url"] = _get_artifact_url(mcfg, "headers")
    # dl_header["header_patches"] = mcfg.header_patches

    # Construct downloads and return it
    downloads = []
    for d in (dl_lib, dl_static, dl_header, dl_sources):
        if d:
            downloads.append(Download(**d))

    return downloads
