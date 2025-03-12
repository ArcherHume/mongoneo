# Import submodules so that we can expose their __all__
from mongoneo import (
    connection,
    document,
    errors,
    fields,
    queryset,
    signals,
    query_builder,
)

# Import everything from each submodule so that it can be accessed via
# mongoneo, e.g. instead of `from mongoneo.connection import connect`,
# users can simply use `from mongoneo import connect`, or even
# `from mongoneo import *` and then `connect('testdb')`.
from mongoneo.connection import *  # noqa: F401
from mongoneo.document import *  # noqa: F401
from mongoneo.errors import *  # noqa: F401
from mongoneo.fields import *  # noqa: F401
from mongoneo.queryset import *  # noqa: F401
from mongoneo.signals import *  # noqa: F401

__all__ = (
    list(document.__all__)
    + list(fields.__all__)
    + list(connection.__all__)
    + list(queryset.__all__)
    + list(signals.__all__)
    + list(errors.__all__)
)


VERSION = (0, 29, 0)


def get_version():
    """Return the VERSION as a string.

    For example, if `VERSION == (0, 10, 7)`, return '0.10.7'.
    """
    return ".".join(map(str, VERSION))


__version__ = get_version()
