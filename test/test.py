"""Automated tests for the blender nif scripts."""

import Blender
from nif_import import NifImport
from nif_export import NifExport
from nif_common import NifConfig

def runtest(test_files):
    """Test the specified files.

    @param test_files: A list of all files to test. Each entry in the list
        is a tuple containing the filename, a dictionary of config options
        that differ from their default values, and a list of names of
        objects to select before running the import. If the dictionary
        has the key EXPORT_VERSION then the selection is exported,
        otherwise a file is imported."""
    scene = Blender.Scene.GetCurrent() # current scene
    layer = 1

    for filename, filecfg, selection in test_files:
        # select objects
        scene.objects.selected = [
            ob for ob in scene.objects if ob.name in selection]

        # set script configuration
        config = dict(**NifConfig.DEFAULTS)
        config["VERBOSITY"] = 99
        for key, value in filecfg.items():
            config[key] = value

        # run test
        if 'EXPORT_VERSION' in filecfg:
            # export the imported files
            print("*** exporting %s ***" % filename)

            config["EXPORT_FILE"] = "nif/%s" % filename
            NifExport(**config)

            # increment active layer for next import
            # different tests are put into different blender layers,
            # so the results can be easily visually inspected
            layer += 1
            scene.setLayers([layer])
        else:
            print("*** importing %s ***" % filename)

            config["IMPORT_FILE"] = "nif/%s" % filename

            # import <filename>
            print "import..."
            NifImport(**config)

    # deselect everything
    scene.objects.selected = []
    # reset active layer
    scene.setLayers([1])
