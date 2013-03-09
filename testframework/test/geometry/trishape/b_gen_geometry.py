import bpy
import math
import mathutils

import nose

EPSILON = 0.005

"""Vertex coordinates for testing."""
b_verts = {
        (-7.5, 7.5, 3.5),
        (7.5, 3.75, 1.75),
        (7.5, -3.75, -1.75),
        (7.5, 3.75, -1.75),
        (-7.5, 7.5, -3.5),
        (-7.5, -7.5, 3.5),
        (7.5, -3.75, 1.75),
        (-7.5, -7.5, -3.5),
        }

def b_create_base_geometry(b_name):
    """Create and return a single polyhedron blender object."""
    b_obj = b_create_cube(b_name)
    b_transform_cube(b_obj)
    return b_obj

def b_create_cube(b_name):
    '''Creates prim Cube, single sided'''

    # create a base mesh, and set its name
    bpy.ops.mesh.primitive_cube_add()
    b_obj = bpy.data.objects[bpy.context.active_object.name]
    b_obj.name = b_name
    
    bpy.ops.object.shade_smooth()
    b_obj.data.show_double_sided = False # b_mesh default: double sided - true, fix this  
    return b_obj

def b_transform_cube(b_obj):
    """ Alters the cube, scaling, transforming """
    
    b_scale_object()
    b_scale_single_face(b_obj)
    b_obj.matrix_local = b_get_transform_matrix()

def b_scale_object():
    """Scale the currently selected object along each axis."""
    
    bpy.ops.transform.resize(value=(7.5,1,1), constraint_axis=(True,False,False))
    bpy.ops.transform.resize(value=(1,7.5,1), constraint_axis=(False,True,False))
    bpy.ops.transform.resize(value=(1,1,3.5), constraint_axis=(False,False,True))
    bpy.ops.object.transform_apply(scale=True)

def b_scale_single_face(b_obj):
    """Scale a single face of the object."""

    # scale single face
    for faces in b_obj.data.faces:
        faces.select = False
    b_obj.data.faces[2].select = True
    
    for b_vert_index in b_obj.data.faces[2].vertices: 
        b_obj.data.vertices[b_vert_index].co[1] = b_obj.data.vertices[b_vert_index].co[1] * 0.5
        b_obj.data.vertices[b_vert_index].co[2] = b_obj.data.vertices[b_vert_index].co[2] * 0.5
                           
def b_get_transform_matrix():
    """Return a non-trivial transform matrix."""
    
    #translation
    b_trans_mat = mathutils.Matrix.Translation((20.0, 20.0, 20.0)) 
    
    #rotation
    b_rot_mat_x = mathutils.Matrix.Rotation(math.radians(30.0), 4, 'X') 
    b_rot_mat_y = mathutils.Matrix.Rotation(math.radians(60.0), 4, 'Y')
    b_rot_mat_z = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')        
    b_rot_mat =  b_rot_mat_x * b_rot_mat_y * b_rot_mat_z
    
    #scale
    b_scale_mat = mathutils.Matrix.Scale(0.75, 4)
    
    b_transform_mat = b_trans_mat * b_rot_mat * b_scale_mat
    return b_transform_mat


def b_check_geom_obj(b_obj):
    b_mesh = b_obj.data
    b_check_transform(b_obj)
    b_check_geom(b_mesh)
    b_check_vertex_count(b_mesh)
    
def b_check_transform(b_obj):
    
    b_loc_vec, b_rot_quat, b_scale_vec = b_obj.matrix_local.decompose() # transforms
    
    nose.tools.assert_equal(b_obj.location, mathutils.Vector((20.0, 20.0, 20.0))) # location
    
    b_rot_quat.to_euler()
    b_rot_eul = b_rot_quat
    nose.tools.assert_equal((b_rot_eul.x - math.radians(30.0)) < EPSILON, True) # x rotation
    nose.tools.assert_equal((b_rot_eul.y - math.radians(60.0)) < EPSILON, True) # y rotation
    nose.tools.assert_equal((b_rot_eul.z - math.radians(90.0)) < EPSILON, True) # z rotation
    
    nose.tools.assert_equal((b_obj.scale - mathutils.Vector((0.75, 0.75, 0.75))) 
            < mathutils.Vector((EPSILON, EPSILON, EPSILON)), True) # uniform scale

def b_check_geom(b_mesh):
    num_triangles = len( [face for face in b_mesh.faces if len(face.vertices) == 3]) # check for tri
    num_triangles += 2 * len( [face for face in b_mesh.faces if len(face.vertices) == 4]) # face = 2 tris
    nose.tools.assert_equal(num_triangles, 12)
    
def b_check_vertex_count(b_mesh):
    nose.tools.assert_equal(len(b_mesh.vertices), 8)
    verts = {
        tuple(round(co, 4) for co in vert.co)
        for vert in b_mesh.vertices
        }
    nose.tools.assert_set_equal(verts, b_verts)
    
