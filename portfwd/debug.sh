#!/bin/bash
exec pip install -e . \
    --no-build-isolation \
    -Csetup-args=-Dbuildtype=debug \
    -Cbuild-dir=build-dbg