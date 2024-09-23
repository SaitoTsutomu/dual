from importlib.metadata import metadata

from .dual import dual, main

__all__ = ["dual", "main"]
_package_metadata = metadata(__package__)
__version__ = _package_metadata["Version"]
__author__ = _package_metadata.get("Author-email", "")
