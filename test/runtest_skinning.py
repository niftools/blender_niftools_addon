"""Automated skinning tests for the blender nif scripts."""

from test import runtest

# some tests to import and export nif files
# as list of (filename, config dictionary, list of objects to be selected)
# if the config has a EXPORT_VERSION key then the test is an export test
# otherwise it's an import test

runtest([
    # oblivion full body
    ('skeleton.nif',  dict(IMPORT_SKELETON = 1), []),
    ('upperbody.nif', dict(IMPORT_SKELETON = 2), ['Scene Root']),
    ('lowerbody.nif', dict(IMPORT_SKELETON = 2), ['Scene Root']),
    ('hand.nif',      dict(IMPORT_SKELETON = 2), ['Scene Root']),
    ('foot.nif',      dict(IMPORT_SKELETON = 2), ['Scene Root']),
    ('_fulloblivionbody.nif',
     dict(
        EXPORT_VERSION = 'Oblivion', EXPORT_SMOOTHOBJECTSEAMS = True,
        EXPORT_FLATTENSKIN = True),
     ['Scene Root']),
    # morrowind creature
    ('babelfish.nif', {}, []),
    ('_babelfish.nif', dict(
        EXPORT_VERSION = 'Morrowind',
        EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
     ['Root Bone']),
    # morrowind better bodies mesh
    ('bb_skinf_br.nif', {}, []),
    ('_bb_skinf_br.nif', dict(
        EXPORT_VERSION = 'Morrowind', EXPORT_SMOOTHOBJECTSEAMS = True,
        EXPORT_STRIPIFY = False, EXPORT_SKINPARTITION = False),
     ['Bip01']),
])
