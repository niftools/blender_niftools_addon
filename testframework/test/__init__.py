"""Package for regression testing of the blender nif scripts."""

import bpy
import io_scene_nif.nif_import
import io_scene_nif.nif_export
import os
import os.path

from pyffi.formats.nif import NifFormat

def clear_bpy_data():
    """Remove all objects from blender."""

    def clear_bpy_prop_collection(collection):
        for elem in collection[:]:
            collection.remove(elem)
    
    def clear_users(collection):
        for elem in collection[:]:
            collection[elem.name].user_clear()
            collection.remove(collection[elem.name])
    
    # unlink objects
    for b_obj in bpy.data.objects[:]:
        bpy.context.scene.objects.unlink(b_obj)
    
    # remove all data
    for collection in (
        "actions", "objects", "meshes", "armatures", "lamps", "lattices",
        "particles", "metaballs", "shape_keys", "texts", "curves",
        "cameras", "grease_pencil", "groups", "libraries",
        "node_groups",
        "materials",
        ):
        clear_bpy_prop_collection(getattr(bpy.data, collection))
    
    # need to remove any users first    
    for collection in (
        "brushes", "textures", "images",
        ):
        clear_users(getattr(bpy.data, collection))

def setup():
    """Enables the nif scripts addon, so all tests can use it."""
    bpy.ops.wm.addon_enable(module="io_scene_nif")
    clear_bpy_data()

def teardown():
    """Disables the nif scripts addon."""
    bpy.ops.wm.addon_disable(module="io_scene_nif")

class Base:
    """Base class for all tests."""
    # Debug Settings
    gen_blender_scene = False
    gen_nifs = False
    
    def b_clear(self):
        """Clear all objects from scene."""
        # ensure in object mode
        # unlinking objects will throw error otherwise 
        if not (bpy.context.mode == 'OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        clear_bpy_data()

    def teardown(self):
        """Called when test finishes, should clean everything to
        prepare for next test.
        """
        self.b_clear()

class SingleNif(Base):
    """Base class for testing a feature concerning single nif files.

    Every test consists of two pieces of data:

    * a nif file (see :attr:`SingleNif.n_create_data`)
    * one or more blender objects (produced by blender code,
      see :meth:`SingleNif.b_create_objects`)

    To construct a new test, you must create a new nif file,
    and overload :meth:`SingleNif.b_create_objects` to match
    the desired imported nif in blender.

    Then, overload the following two methods for checking this data:

    * :meth:`SingleNif.b_check_data`
    * :meth:`SingleNif.n_check_data`

    Two tests will be run
    (see implementation of :meth:`SingleNif.test_import_export`
    and :meth:`SingleNif.test_export_import`):

    1. Check nif data to be imported,
       import nif,
       check imported blender data,
       export it again,
       check exported nif data.

    2. Create blender objects,
       check blender data to be exported,
       export to nif,
       check exported nif data,
       import the nif just exported,
       check imported blender data.

    """

    n_name = None
    """Base name of nif file (without ``0.nif`` at the end)."""

    EPSILON = 0.005
    """A small value used when comparing floats."""

    n_filepath_0 = None
    """The name of the nif file to import
    (set automatically from :attr:`SingleNif.n_name`).
    """

    n_filepath_1 = None
    """The name of the nif file to export from import
    (set automatically from :attr:`SingleNif.n_name`).
    """

    n_filepath_2 = None
    """The name of the nif file to export from created blender scene
    (set automatically from :attr:`SingleNif.n_name`).
    """

    b_filepath_0 = None
    """The name of the blend file after importing *n_filepath_0*
    (set automatically from :attr:`SingleNif.n_name`).
    """

    b_filepath_1 = None
    """The name of the blend file resulting from *b_create_objects*
    (set automatically from :attr:`SingleNif.n_name`).
    """

    b_filepath_2 = None
    """The name of the blend file after import of *n_filepath_2*
    (set automatically from :attr:`SingleNif.n_name`).
    """

    def __init__(self):
        """Initialize the test."""
        Base.__init__(self)
                
        self.n_filepath_0 = "test/nif/" + self.n_name + "0.nif"
        self.n_filepath_1 = "test/nif/" + self.n_name + "1.nif"
        self.n_filepath_2 = "test/nif/" + self.n_name + "2.nif"

        self.b_filepath_0 = "test/autoblend/" + self.n_name + "0.blend"
        self.b_filepath_1 = "test/autoblend/" + self.n_name + "1.blend"
        self.b_filepath_2 = "test/autoblend/" + self.n_name + "2.blend"

    def _b_clear_check(self, b_obj_names):
        """Check that *b_obj_names* are really cleared from the scene."""
        try:
            for name in b_obj_names:
                b_obj = bpy.data.objects[name]
        except KeyError:
            pass
        else:
            raise RuntimeError(
                "failed to clear {0} from scene".format(b_obj))

    def _b_select_all(self):
        """Select all objects, and return their names."""
        b_obj_names = []
        for b_obj in bpy.data.objects:
            b_obj.select = True
            b_obj_names.append(b_obj.name)
        return b_obj_names

    def b_create_objects(self):
        """Create blender objects for feature."""
        raise NotImplementedError

    def b_save(self, b_filepath):
        """Save current scene to blend file."""
        if not os.path.exists(os.path.dirname(b_filepath)):
            os.makedirs(os.path.dirname(b_filepath))
        bpy.ops.wm.save_mainfile(filepath=b_filepath)

    def b_check_data(self):
        """Check blender objects against feature."""
        raise NotImplementedError

    def n_create_data(self):
        """Create and return nif data used for initial nif file."""
        raise NotImplementedError

    def n_check_data(self, n_data):
        """Check nif data against feature."""
        raise NotImplementedError

    def n_check(self, n_filepath):
        """Check nif file against feature."""
        self.n_check_data(self.n_read(n_filepath))

    def n_read(self, n_filepath):
        """Read nif file and return the data."""
        n_data = NifFormat.Data()
        with open(n_filepath, "rb") as stream:
            n_data.read(stream)
        return n_data
    
    def n_write(self, n_data, n_filepath):
        """Write a nif file from data."""
        with open(n_filepath, "wb") as stream:
            n_data.write(stream)

    def n_import(self, n_filepath):
        """Import nif file."""
        bpy.ops.import_scene.nif(
            filepath=n_filepath,
            log_level='DEBUG',
            )

    def n_export(self, n_filepath):
        """Export selected blender object to nif file."""
        bpy.ops.export_scene.nif(
            filepath=n_filepath,
            log_level='DEBUG',
            )

    def test_import_export(self):
        """Test import followed by export."""
        # create initial nif file and check data
        self.n_write(self.n_create_data(), self.n_filepath_0)
        self.n_check(self.n_filepath_0)
        
        # import nif and check data
        self.b_clear()
        self.n_import(self.n_filepath_0)
        b_obj_names = self._b_select_all()
        self.b_save(self.b_filepath_0)
        self.b_check_data()
        
        # export and check data
        self.n_export(self.n_filepath_1)
        self.n_check(self.n_filepath_1)
        self.b_clear()
        self._b_clear_check(b_obj_names)

    def test_export_import(self):
        """Test export followed by import."""
        
        # create scene
        self.b_create_objects()
        b_obj_names = self._b_select_all()
        self.b_save(self.b_filepath_1)
        self.b_check_data()
        
        # export and check data
        self.n_export(self.n_filepath_2)
        self.n_check(self.n_filepath_2)
        self.b_clear()
        self._b_clear_check(b_obj_names)
        
        # import and check data
        self.n_import(self.n_filepath_2)
        b_obj_names = self._b_select_all()
        self.b_save(self.b_filepath_2)
        self.b_check_data()
        self.b_clear()
        self._b_clear_check(b_obj_names)
