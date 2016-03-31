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
    
    Each new feature test inherits from SingleNif.
    SingleNif will take care of loading nifs, running import, object clean-up.
    
    Every test must define the following attributes
    
    * :attr: `SingleNif.n_name` - sets path where to generate files. 
    
    Every test needs to implement four functions, with specific behaviour for that test:
    
    * :meth:`SingleNif.n_create_data` - Python code used to create a physical nif
    
    * :meth:`SingleNif.n_check_data` - Used to check a physical nif contain information as expected
    
    * :meth:`SingleNif.b_create_data` - Setup Blender scene as user would with the same information as physical nif
    
    * :meth:`SingleNif.b_check_data` - Check that the scene contains contains the information as expected.
   
    If features can be reused, then they should be put into a b_gen_xxx or n_gen_xxx file, rather than kept in the test itself.
    This reduces both the test complexity and avoids issues where tests are re-run if they are imported.
    
    Execution Order:
       
    Two tests are run (see implementation of :meth:`SingleNif.test_pycode_nif`
    and :meth:`SingleNif.test_user_nif`):

    1. 
        * Create Physical Nif
        * Check nif data,
        * Import nif,
        * Check blender scene data,
        * Export nif,
        * Check exported nif data.

    2. 
        * Create Blender scene
        * Check Blender scene data,
        * Export nif,
        * Check exported nif data,
        * Import nif,
        * Check Blender scene data,

    """

    n_name = None
    """Base name of nif file (without ``0.nif`` at the end)."""

    n_data = None
    """Store the nif as it generate, built in blocks. Useful to see generated nif in-memory"""
    
    EPSILON = 0.005
    """A small value used when comparing floats."""

    n_game = 'OBLIVION'
    """Game for nif export."""

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
    """The name of the blend file resulting from *b_create_data*
    (set automatically from :attr:`SingleNif.n_name`).
    """

    b_filepath_2 = None
    """The name of the blend file after import of *n_filepath_2*
    (set automatically from :attr:`SingleNif.n_name`).
    """
    
    # Debug Settings
    gen_blender_scene = True
    
    def __init__(self):
        """Initialize the test."""
        Base.__init__(self)
        
        self.n_data = NifFormat.Data()
        
        root = "integration/gen/"
        nif_path = root + "nif/" + self.n_name
        blend_path = root + "autoblend/" + self.n_name
        
        self.n_filepath_0 = nif_path + "_py_code.nif"
        self.n_filepath_1 = nif_path + "_export_py_code.nif"
        self.n_filepath_2 = nif_path + "_export_user_ver.nif"

        self.b_filepath_0 = blend_path + "_pycode_import.blend"
        self.b_filepath_1 = blend_path + "_userver.blend"
        self.b_filepath_2 = blend_path + "_userver_reimport.blend"
        self.b_filepath_except = blend_path + "_exception.blend"

        if not os.path.exists(nif_path):
            os.makedirs(nif_path)

        if not os.path.exists(blend_path):
            os.makedirs(blend_path)

    def _b_clear_check(self, b_obj_names):
        """Check that *b_obj_names* are really cleared from the scene."""
        if(len(b_obj_names) != 0):
            try:
                for name in b_obj_names:
                    bpy.data.objects[name]
            except KeyError:
                pass
            else:
                print(b_obj_names)
                self.b_save(self.b_filepath_except)
                raise RuntimeError("failed to clear objects from scene")

    def _b_select_all(self):
        """Select all objects, and return their names."""
        b_obj_names = []
        print("Objects in scene - {0}".format(len(bpy.data.objects)))
        for b_obj in bpy.data.objects:
            print("Scene Object - " + b_obj.name)
            b_obj.select = True
            b_obj_names.append(b_obj.name)
        return b_obj_names

    def b_save(self, b_filepath):
            """Save current scene to blend file."""
            bpy.ops.wm.save_mainfile(filepath=b_filepath)

    def b_create_header(self):
        """Select game version to export as"""
        raise NotImplementedError

    def b_create_data(self):
        """Create blender objects for feature."""
        raise NotImplementedError

    def b_check_data(self):
        """Check blender objects against feature."""
        raise NotImplementedError

    def n_create_header(self):
        """Create header"""
        raise NotImplementedError

    def n_create_data(self):
        """Create and return nif data used for initial nif file."""
        raise NotImplementedError

    def n_check_data(self):
        """Check nif data against feature."""
        raise NotImplementedError

    def n_check(self, n_filepath):
        """Check nif file against feature."""
        self.n_data = self.n_read(n_filepath)
        self.n_check_data()

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
        print("Export Options {0}, {1}".format(n_filepath, self.n_game))
        bpy.ops.export_scene.nif(filepath=n_filepath,
                                 log_level='DEBUG',
                                 game=self.n_game,
                                 )

    def test_export_user(self):       
        """User : Export user generated file"""
        
        # create scene
        self.b_create_header()
        self.b_create_data()
        if(self.gen_blender_scene):
            self.b_save(self.b_filepath_1)
        self.b_check_data()
        
        # export and check data
        self.n_export(self.n_filepath_2)
        self.n_check(self.n_filepath_2)
    
    def test_import_user(self):     
        """User : Import user generated file"""
        # import and check data
        self.n_import(self.n_filepath_2)
        if(self.gen_blender_scene):
            self.b_save(self.b_filepath_2)
        self.b_check_data()
         
    def test_pycode_nif_fullflow(self):
        """PyCode : Import/Export python generated file"""
        # create initial nif file and check data
        self.n_write(self.n_create_data(), self.n_filepath_0)
        self.n_check(self.n_filepath_0)
           
        # clear scene
        self.b_clear()
          
        # import nif and check data
        self.n_import(self.n_filepath_0)
        if(self.gen_blender_scene):
            self.b_save(self.b_filepath_0)
        self.b_check_data()
        
        self._b_select_all()
        
        # export and check data
        self.n_export(self.n_filepath_1)
        self.n_check(self.n_filepath_1)
           
