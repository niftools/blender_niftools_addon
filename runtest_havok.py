"""Automated havok tests for the blender nif scripts."""

from nif_test import runtest

# some tests to import and export nif files
# as list of (filename, config dictionary, list of objects to be selected)
# if the config has a EXPORT_VERSION key then the test is an export test
# otherwise it's an import test

runtest("test/nif", [
    ('battleaxe.nif', {}, []),
    ('_battleaxe.nif',
     dict(EXPORT_VERSION = 'Oblivion',
          EXPORT_OB_LAYER = 5, # weapon
          EXPORT_BHKLISTSHAPE = True,
          EXPORT_OB_MASS = 23.0),
     ['BattleAxe']),
    ('crystalball02.nif', {}, []),
    ('_crystalball02.nif',
     dict(EXPORT_VERSION = 'Oblivion',
          EXPORT_BHKLISTSHAPE = True,
          EXPORT_OB_LAYER = 4, # clutter
          EXPORT_OB_MASS = 9.5),
     ['CrystalBall02']),
    ('anvilcirclebench01.nif', {}, []),
    ('_anvilcirclebench01.nif',
     dict(EXPORT_VERSION = 'Oblivion'),
     ['AnvilCircleBench01']),
    ('frostatron.nif', {}, []),
    ('_frostatron.nif',
     dict(EXPORT_VERSION = 'Oblivion'),
     ['FrostAtron'])
])
