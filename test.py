"""Automated tests for the blender nif scripts."""

import Blender
from nif_import import NifImport
from nif_export import NifExport
from nif_common import NifConfig

SCENE = Blender.Scene.GetCurrent() # current scene
LAYER = 1

# some tests to import and export nif files
# as list of (filename, config dictionary, list of objects to be selected)
# if the config has a EXPORT_VERSION key then the test is an export test
# otherwise it's an import test
TEST_FILES = [
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
]

for filename, filecfg, selection in TEST_FILES:
    # select objects
    SCENE.objects.selected = [
        ob for ob in SCENE.objects if ob.name in selection]

    # set script configuration
    config = dict(**NifConfig.DEFAULTS)
    config["VERBOSITY"] = 99
    for key, value in filecfg.items():
        config[key] = value

    # run test
    if 'EXPORT_VERSION' in filecfg:
        # export the imported files
        print "*** exporting %s ***" % filename

        config["EXPORT_FILE"] = "test/nif/%s" % filename
        NifExport(**config)

        # deselect everything before changing active layer
        # (otherwise objects do not get placed in the correct layer)
        SCENE.objects.selected = []

        # increment active layer for next import
        # different tests are put into different blender layers,
        # so the results can be easily visually inspected
        LAYER += 1
        SCENE.setLayers([LAYER])
    else:
        print "*** importing %s ***" % filename

        config["IMPORT_FILE"] = "test/nif/%s" % filename

        # import <filename>
        print "import..."
        NifImport(**config)

    # deselect everything
    SCENE.objects.selected = []
    # reset active layer
    SCENE.setLayers([1])
