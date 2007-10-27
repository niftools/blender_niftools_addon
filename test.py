# blender scripts tests

import Blender
from nif_import import NifImport
from nif_export import NifExport
from nif_common import NifConfig

scene = Blender.Scene.GetCurrent() # current scene
layer = 1 # current layer (each test gets its layer)

# some tests to import and export nif files

test_files = [
    ('babelfish.nif', dict(EXPORT_VERSION = 'Morrowind')),
    ('bb_skinf_br.nif', dict(
        EXPORT_VERSION = 'Morrowind', EXPORT_SMOOTHOBJECTSEAMS = True)),
]

for filename, filecfg in test_files:
    print "*** testing: %s ***"%filename

    # set script configuration
    config = dict(**NifConfig.DEFAULTS)
    config["VERBOSITY"] = 99
    for key, value in filecfg.items():
        config[key] = value

    config["IMPORT_FILE"] = "test/nif/%s"%filename
    config["EXPORT_FILE"] = "test/nif/_%s"%filename

    # unselect all objects
    scene.objects.selected = []

    # select layer: put different import tests into different blender layers,
    # so the imports can be visually inspected
    scene.setLayers([layer+1]) # layers are numbered from 1 till 20

    # import <filename>
    print "import..."
    NifImport(**config)

    # export the imported file as _<filename>
    print "export..."
    NifExport(**config)

    layer += 1

