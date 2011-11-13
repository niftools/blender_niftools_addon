"""Package for regression testing of the blender nif scripts."""

import bpy
import io_scene_nif.import_nif
import io_scene_nif.export_nif

from pyffi.formats.nif import NifFormat

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

    n_name = None
    """Name of nif file (without ``0.nif`` at the end)."""

    b_name = None
    """Name of imported blender object."""

    def __init__(self):
        Base.__init__(self)
        self.n_filepath_0 = "test/nif/" + self.n_name + "0.nif"
        self.n_filepath_1 = "test/nif/" + self.n_name + "1.nif"
        self.n_filepath_2 = "test/nif/" + self.n_name + "2.nif"

    def b_create(self):
        """Create and return blender object for feature."""
        raise NotImplementedError

    def b_check(self, b_obj):
        """Check blender object against feature."""
        raise NotImplementedError

    def n_check_data(self, n_data):
        """Check nif data against feature."""
        raise NotImplementedError

    def n_check(self, n_filepath):
        """Check nif file against feature."""
        self.n_check_data(self.n_read(n_filepath))

    def n_read(self, n_filepath):
        n_data = NifFormat.Data()
        with open(n_filepath, "rb") as stream:
            n_data.read(stream)
        return n_data

    def n_import(self, n_filepath):
        bpy.ops.import_scene.nif(
            filepath=n_filepath,
            log_level='DEBUG',
            )

    def n_export(self, n_filepath):
        bpy.ops.export_scene.nif(
            filepath=n_filepath,
            log_level='DEBUG',
            )

    def test_import_export(self):
        self.b_clear()
        self.n_check(self.n_filepath_0)
        self.n_import(self.n_filepath_0)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check(b_obj)
        b_obj.select = True
        self.n_export(self.n_filepath_1)
        self.n_check(self.n_filepath_1)

    def test_export_import(self):
        b_obj = self.b_create()
        self.b_check(b_obj)
        b_obj.select = True
        self.n_export(self.n_filepath_2)
        self.n_check(self.n_filepath_2)
        self.b_clear()
        self.n_import(self.n_filepath_2)
        b_obj = bpy.data.objects[self.b_name]
        self.b_check(b_obj)
