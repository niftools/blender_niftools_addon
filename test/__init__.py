"""Package for regression testing of the blender nif scripts."""

import bpy

def clean_bpy_data():
    """Remove all objects from blender."""

    def clean_bpy_prop_collection(collection):
        for elem in collection[:]:
            collection.remove(elem)

    # unlink objects
    for obj in bpy.data.objects[:]:
        bpy.context.scene.objects.unlink(obj)
    # remove all data
    for collection in (
        "objects", "meshes", "armatures", "images", "lamps", "lattices",
        "materials", "particles", "metaballs", "shape_keys", "texts",
        "textures",
        ):
        clean_bpy_prop_collection(getattr(bpy.data, collection))

def setup():
    """Enables the nif scripts addon, so all tests can use it."""
    bpy.ops.wm.addon_enable(module="io_scene_nif")
    clean_bpy_data()

def teardown():
    """Disables the nif scripts addon."""
    bpy.ops.wm.addon_disable(module="io_scene_nif")

class Test:
    """Base class for all tests."""
    def teardown(self):
        clean_bpy_data()
