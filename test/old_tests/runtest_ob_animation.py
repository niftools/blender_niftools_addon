"""Automated animation tests for the blender nif scripts."""

import os.path

from nif_test import TestSuite
from nif_common import NifFormat

# some tests to import and export nif files
# as list of (filename, config dictionary, list of objects to be selected)
# if the config has a game key then the test is an export test
# otherwise it's an import test

class TestSuiteAnimation(TestSuite):
    def run(self):
        ob_male = os.path.join(
            self.config.get("path", "oblivion"),
            "meshes", "characters", "_male")
        self.test(
            filename=os.path.join(ob_male, 'skeleton.nif'),
            config=dict(
                # we also import havok, for regression testing
                # uncomment next line for testing without havok
                #IMPORT_SKELETON=1,
                IMPORT_KEYFRAMEFILE=os.path.join(ob_male, 'castself.kf')))
        self.test(
            filename='test/nif/_castself.kf',
            config=dict(
                game = 'OBLIVION',
                animation='ANIM_KF', # animation only
                EXPORT_OB_LAYER = NifFormat.OblivionLayer.OL_BIPED),
             selection=['Scene Root'])

suite = TestSuiteAnimation("animation")
suite.run()
