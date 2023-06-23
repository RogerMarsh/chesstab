# filespec.py
# Copyright 2023 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Files and fields for chess database.

Overrule field naming choices in core.filespec.FileSpec so DPT Fastload
can succeed.

DPT Fastload does not work with field names that are not upper case.

DPT restricts just the first character of field names to be upper case in
all other respects.

"""
from solentware_base.core.constants import (
    PRIMARY,
    SECONDARY,
    FIELDS,
)

from ..core import filespec


class FileSpec(filespec.FileSpec):
    """Extend to support DPT Fastload."""

    def __init__(self, **kargs):
        """Define chess database with upper case field names."""
        super().__init__(**kargs)
        for file in self.values():
            file[PRIMARY] = file[PRIMARY].upper()
            file[SECONDARY] = {
                key: key.upper() if value is None else value.upper()
                for key, value in file[SECONDARY].items()
            }
            file[FIELDS] = {
                key.upper(): value for key, value in file[FIELDS].items()
            }
