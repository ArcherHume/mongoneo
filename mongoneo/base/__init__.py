# Base module is split into several files for convenience. Files inside of
# this module should import from a specific submodule (e.g.
# `from mongoneo.base.document import BaseDocument`), but all of the
# other modules should import directly from the top-level module (e.g.
# `from mongoneo.base import BaseDocument`). This approach is cleaner and
# also helps with cyclical import errors.
from mongoneo.base.common import *
from mongoneo.base.datastructures import *
from mongoneo.base.document import *
from mongoneo.base.fields import *
from mongoneo.base.metaclasses import *

__all__ = (
    # common
    "UPDATE_OPERATORS",
    "_DocumentRegistry",
    # datastructures
    "BaseDict",
    "BaseList",
    "EmbeddedDocumentList",
    "LazyReference",
    # document
    "BaseDocument",
    # fields
    "BaseField",
    "ComplexBaseField",
    "ObjectIdField",
    "GeoJsonBaseField",
    # metaclasses
    "DocumentMetaclass",
    "TopLevelDocumentMetaclass",
)
