"""Import and export full body (bind pose) nif for Fallout 3."""

from __future__ import with_statement
import logging
import os.path

from pyffi.formats.nif import NifFormat

from nif_test import TestSuite

class Fallout3FullBodyTestSuite(TestSuite):
    def run(self):
        self.make_fo3_fullbody()
        self.test(
            filename="test/nif/fo3/_fullbody.nif",
            config=dict(
                IMPORT_TEXTURE_PATH=[self.config.get("path", "fallout3")]))
        # just checking that export works
        self.test(
            filename="test/nif/fo3/__fullbody.nif",
            config=dict(EXPORT_VERSION='Fallout 3'),
            selection=['Scene Root'])

suite = Fallout3FullBodyTestSuite("fo3_animation")
suite.run()
