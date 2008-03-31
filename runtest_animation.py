"""Automated animation tests for the blender nif scripts."""

from nif_test import runtest

# some tests to import and export nif files
# as list of (filename, config dictionary, list of objects to be selected)
# if the config has a EXPORT_VERSION key then the test is an export test
# otherwise it's an import test

runtest("test/nif", [
    # oblivion animation
    ('skeleton.nif',
     dict(IMPORT_SKELETON = 1,
          IMPORT_KEYFRAMEFILE = 'test/nif/castself.kf'), []),
    ('_castself.kf',
     dict(EXPORT_VERSION = 'Oblivion',
          EXPORT_ANIMATION = 2), # animation only
     ['Scene Root']),
])
