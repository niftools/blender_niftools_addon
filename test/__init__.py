"""Package for regression testing of the blender nif scripts."""

import bpy
import io_scene_nif.import_nif
import io_scene_nif.export_nif

def clear_bpy_data():
    """Remove all objects from blender."""

    def clear_bpy_prop_collection(collection):
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
        clear_bpy_prop_collection(getattr(bpy.data, collection))

def setup():
    """Enables the nif scripts addon, so all tests can use it."""
    bpy.ops.wm.addon_enable(module="io_scene_nif")
    clear_bpy_data()

def teardown():
    """Disables the nif scripts addon."""
    bpy.ops.wm.addon_disable(module="io_scene_nif")

class Base:
    """Base class for all tests."""

    def b_clear(self):
        clear_bpy_data()

    def teardown(self):
        clear_bpy_data()

class SingleNif(Base):
    """Base class for testing a feature concerning single nif files."""
    name = None
    """Feature name (serves as part of filepath, string, no spaces or
    special characters).
    """

    def __init__(self):
        if self.name is None:
            return
        Test.__init__(self)
        n_filepath_0 = "test/nif/" + self.name + "0.nif"
        n_filepath_1 = "test/nif/" + self.name + "1.nif"
        n_filepath_2 = "test/nif/" + self.name + "2.nif"

    def b_create(self):
        """Create blender objects in current blender scene for feature."""
        raise NotImplementedError

    def b_check(self):
        """Check current blender scene against feature."""
        raise NotImplementedError

    def n_check(self, n_filepath):
        """Check nif file against feature."""
        raise NotImplementedError

    def n_import(self, n_filepath):
        io_scene_nif.import_scene.nif(
            filepath=n_filepath,
            log_level='DEBUG',
            )

    def n_export(self, n_filepath):
        io_scene_nif.export_scene.nif(
            filepath=n_filepath,
            log_level='DEBUG',
            )

    def test_import_export(self):
        self.b_clear()
        self.n_check(self.n_filepath_0)
        self.n_import(self.n_filepath_0)
        self.b_check()
        self.n_export(self.n_filepath_1)
        self.n_check(self.n_filepath_1)

    def test_export_import(self):
        self.b_create()
        self.b_check()
        self.n_export(self.n_filepath_2)
        self.n_check(self.n_filepath_2)
        self.b_clear()
        self.n_import(self.n_filepath_2)
        self.b_check()
