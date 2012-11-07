"""Exports and imports mesh data"""

import bpy
import nose.tools
import math
import mathutils

from test import Base, SingleNif
from pyffi.formats.nif import NifFormat

class TestBaseGeometry(SingleNif):
    """Test base geometry, single blender object."""

    # (documented in SingleNif)
    n_name = "geometry/base_geometry"

    b_name = 'Cube'
    """Name of the blender object.
    This is automatically appended to :attr:`SingleNif.b_obj_list`
    during :meth:`TestBaseGeometry.b_create_objects`.
    """
    # TODO maybe __init__ is the more logical place to set b_obj_list?

    def b_create_objects(self):
        """Register :attr:`b_name`, and call :meth:`b_create_base_geometry`.
        """
        self.b_obj_list.append(self.b_name)
        self.b_create_base_geometry()
        
    def b_create_base_geometry(self):
        """Create a single polyhedron blender object."""

        # create a base mesh, and set its name
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects[bpy.context.active_object.name]
        b_obj.name = self.b_name

        # transform it into something less trivial
        self.scale_object(b_obj)
        self.scale_single_face(b_obj)
        b_obj.matrix_local = self.transform_matrix()

        # primitive_cube_add sets double sided flag, fix this
        b_obj.data.show_double_sided = False
        
        # bpy.ops.wm.save_mainfile(filepath="test/autoblend/" + self.n_name)

    # TODO b_scale_object
    def scale_object(self, b_obj):
        """Scale the object differently along each axis."""

        bpy.ops.transform.resize(value=(7.5,1,1), constraint_axis=(True,False,False))
        bpy.ops.transform.resize(value=(1,7.5,1), constraint_axis=(False,True,False))
        bpy.ops.transform.resize(value=(1,1,3.5), constraint_axis=(False,False,True))
        bpy.ops.object.transform_apply(scale=True)

    # TODO b_scale_single_face
    def scale_single_face(self, b_obj):
        """Scale a single face of the object."""

        # scale single face
        for faces in b_obj.data.faces:
            faces.select = False
        b_obj.data.faces[2].select = True
        
        for b_vert_index in b_obj.data.faces[2].vertices: 
            b_obj.data.vertices[b_vert_index].co[1] = b_obj.data.vertices[b_vert_index].co[1] * 0.5
            b_obj.data.vertices[b_vert_index].co[2] = b_obj.data.vertices[b_vert_index].co[2] * 0.5
                                 
    # TODO b_get_transform_matrix
    def transform_matrix(self):
        """Return a non-trivial transform matrix."""
        
        b_trans_mat = mathutils.Matrix.Translation((20.0, 20.0, 20.0)) 
        
        b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X') 
        b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
        b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')        
        b_rot_mat =  b_rot_mat_x * b_rot_mat_y * b_rot_mat_z
        
        b_scale_mat = mathutils.Matrix.Scale(0.75, 4)
        
        b_transform_mat = b_trans_mat * b_rot_mat * b_scale_mat
        return b_transform_mat
    
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        self.b_check_rotation(b_obj)
        b_mesh = b_obj.data
        self.b_check_geom(b_mesh)

    # b_check_transform?
    def b_check_rotation(self, b_obj):
        
        b_loc_vec, b_rot_quat, b_scale_vec = b_obj.matrix_local.decompose() # transforms
        
        nose.tools.assert_equal(b_obj.location, mathutils.Vector((20.0, 20.0, 20.0))) # location
        
        b_rot_quat.to_euler()
        b_rot_eul = b_rot_quat
        nose.tools.assert_equal((b_rot_eul.x - math.radians(30.0)) < self.EPSILON, True) # x rotation
        nose.tools.assert_equal((b_rot_eul.y - math.radians(60.0)) < self.EPSILON, True) # y rotation
        nose.tools.assert_equal((b_rot_eul.z - math.radians(90.0)) < self.EPSILON, True) # z rotation
        nose.tools.assert_equal((b_obj.scale - mathutils.Vector((0.75, 0.75, 0.75))) 
                < mathutils.Vector((self.EPSILON,self.EPSILON,self.EPSILON)), True) # uniform scale
        
    def b_check_geom(self, b_mesh):
        num_triangles = len( [face for face in b_mesh.faces if len(face.vertices) == 3]) # check for tri
        num_triangles += 2 * len( [face for face in b_mesh.faces if len(face.vertices) == 4]) # face = 2 tris
        nose.tools.assert_equal(len(b_mesh.vertices), 8)
        nose.tools.assert_equal(num_triangles, 12)
        # TODO also check location of vertices

    def n_check_data(self, n_data):
        n_trishape = n_data.roots[0].children[0]
        self.n_check_trishape(n_trishape)
        self.n_check_transform(n_trishape)
        self.n_check_trishape_data(n_trishape.data)

    def n_check_trishape(self, n_geom):
        nose.tools.assert_is_instance(n_geom, NifFormat.NiTriShape)

    def n_check_transform(self, n_geom):        
        nose.tools.assert_equal(n_geom.translation.as_tuple(),(20.0, 20.0, 20.0)) # location
        
        n_rot_eul = mathutils.Matrix(n_geom.rotation.as_tuple()).to_euler()
        nose.tools.assert_equal((n_rot_eul.x - math.radians(30.0)) < self.EPSILON, True) # x rotation
        nose.tools.assert_equal((n_rot_eul.y - math.radians(60.0)) < self.EPSILON, True) # y rotation
        nose.tools.assert_equal((n_rot_eul.z - math.radians(90.0)) < self.EPSILON, True) # z rotation
        
        nose.tools.assert_equal(n_geom.scale - 0.75 < self.EPSILON, True) # scale
    
    def n_check_trishape_data(self, n_trishape_data):
        nose.tools.assert_equal(n_trishape_data.num_vertices, 8)
        nose.tools.assert_equal(n_trishape_data.num_triangles, 12)
        # TODO also check location of vertices
        
    '''
        TODO: Additional checks needed.
        
        TriData
            Flags: blender exports| Continue, Maya| Triangles, Pyffi| Bound.
            Consistancy:
            radius:
    '''

class TestNonUniformlyScaled(Base):
    def setup(self):
        # create a non-uniformly scaled cube
        bpy.ops.mesh.primitive_cube_add()
        b_obj = bpy.data.objects["Cube"]
        b_obj.scale = (1, 2, 3)

    @nose.tools.raises(Exception)
    def test_export(self):
        bpy.ops.export_scene.nif(
            filepath="test/export/non_uniformly_scaled_cube.nif",
            log_level='DEBUG',
            )

