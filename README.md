hatch and pkgconf and meson demo
================================

In a new virtualenv:

    pip install editables hatchling hatch-vcs meson meson-python pkgconf

    pushd robotpy-pybind11
    pip install -e . --no-build-isolation
    popd

    pushd hatch-robotpy
    pip install -e . --no-build-isolation
    popd

    pushd hatch-mkpkgconf
    pip install -e . --no-build-isolation
    popd

    pushd native.wpiutil
    pip install -e . --no-build-isolation
    popd

    pushd native.wpinet
    pip install -e . --no-build-isolation
    popd

    pushd portfwd
    pip install -e . --no-build-isolation
    popd

To show that it's working:

    python3 portfwd/t.py