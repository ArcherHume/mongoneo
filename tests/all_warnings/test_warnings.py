"""
This test has been put into a module.  This is because it tests warnings that
only get triggered on first hit.  This way we can ensure its imported into the
top level and called first by the test suite.
"""

import unittest
import warnings

from mongoneo import *


class TestAllWarnings(unittest.TestCase):
    def setUp(self):
        connect(db="mongoneotest")
        self.warning_list = []
        self.showwarning_default = warnings.showwarning
        warnings.showwarning = self.append_to_warning_list

    def append_to_warning_list(self, message, category, *args):
        self.warning_list.append({"message": message, "category": category})

    def tearDown(self):
        # restore default handling of warnings
        warnings.showwarning = self.showwarning_default

    def test_document_collection_syntax_warning(self):
        class NonAbstractBase(Document):
            meta = {"allow_inheritance": True}

        class InheritedDocumentFailTest(NonAbstractBase):
            meta = {"collection": "fail"}

        warning = self.warning_list[0]
        assert SyntaxWarning == warning["category"]
        assert "non_abstract_base" == InheritedDocumentFailTest._get_collection_name()
