import pytest

from mongoneo import Document
from mongoneo.common import _import_class


class TestCommon:
    def test__import_class(self):
        doc_cls = _import_class("Document")
        assert doc_cls is Document

    def test__import_class_raise_if_not_known(self):
        with pytest.raises(ValueError):
            _import_class("UnknownClass")
