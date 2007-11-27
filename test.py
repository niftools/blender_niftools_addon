"""Automated tests for the blender nif scripts."""

import Blender
from nif_import import NifImport
from nif_export import NifExport
from nif_common import NifConfig

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

class Test:
    """A class for running import and export tests with Blender."""
    def __init__(self):
        """Initialize the tester."""
        self.scene = Blender.Scene.GetCurrent() # current scene
        self.layer = 1

    def run(self, test_files):
        """Test the specified files.

        @param test_files: A list of all files to test. Each entry in the list
            is a tuple containing the filename, a dictionary of config options
            that differ from their default values, and a list of names of
            objects to select before running the import. If the dictionary
            has the key EXPORT_VERSION then the selection is exported,
            otherwise a file is imported."""
        for filename, filecfg, selection in test_files:
            # select objects
            self.scene.objects.selected = [
                ob for ob in self.scene.objects if ob.name in selection]

            # set script configuration
            config = dict(**NifConfig.DEFAULTS)
            config["VERBOSITY"] = 99
            for key, value in filecfg.items():
                config[key] = value

            # run test
            if 'EXPORT_VERSION' in filecfg:
                # export the imported files
                print("*** exporting %s ***" % filename)

                config["EXPORT_FILE"] = "test/nif/%s" % filename
                NifExport(**config)

                # increment active layer for next import
                # different tests are put into different blender layers,
                # so the results can be easily visually inspected
                self.layer += 1
                self.scene.setLayers([self.layer])
            else:
                print("*** importing %s ***" % filename)

                config["IMPORT_FILE"] = "test/nif/%s" % filename

                # import <filename>
                print "import..."
                NifImport(**config)

        # deselect everything
        self.scene.objects.selected = []
        # reset active layer
        self.scene.setLayers([1])
