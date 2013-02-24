import math
import mathutils

import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

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


def n_create_blocks(n_data):
    n_ninode_1 = NifFormat.NiNode()
    n_nitrishape_1 = NifFormat.NiTriShape()
    n_nitrishapedata_1 = NifFormat.NiTriShapeData()
    n_data.roots = [n_ninode_1]

    with ref(n_ninode_1) as n_ninode:
        n_ninode.name = b'Scene Root'
        n_ninode.flags = 14
        with ref(n_ninode.rotation) as n_matrix33:
            n_matrix33.m_11 = 1
            n_matrix33.m_22 = 1
            n_matrix33.m_33 = 1
        n_ninode.scale = 1
        n_ninode.num_children = 1
        n_ninode.children.update_size()
        n_ninode.children[0] = n_nitrishape_1
    with ref(n_nitrishape_1) as n_nitrishape:
        n_nitrishape.name = b'Cube'
        n_nitrishape.flags = 14
        with ref(n_nitrishape.translation) as n_vector3:
            n_vector3.x = 20
            n_vector3.y = 20
            n_vector3.z = 20
        with ref(n_nitrishape.rotation) as n_matrix33:
            n_matrix33.m_11 = 0
            n_matrix33.m_21 = -0.5
            n_matrix33.m_31 = 0.866025
            n_matrix33.m_12 = 0.866025
            n_matrix33.m_22 = -0.433013
            n_matrix33.m_32 = -0.25
            n_matrix33.m_13 = 0.5
            n_matrix33.m_23 = 0.75
            n_matrix33.m_33 = 0.433012
            # just to make sure in case we change values:
            assert(n_matrix33.is_rotation())
        n_nitrishape.scale = 0.75
        n_nitrishape.data = n_nitrishapedata_1
        
    with ref(n_nitrishapedata_1) as n_nitrishapedata:
        n_nitrishapedata.num_vertices = 8
        n_nitrishapedata.has_vertices = True
        n_nitrishapedata.vertices.update_size()
        with ref(n_nitrishapedata.vertices[0]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[1]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = -1.75
        with ref(n_nitrishapedata.vertices[2]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[3]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = -3.5
        with ref(n_nitrishapedata.vertices[4]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = 1.75
        with ref(n_nitrishapedata.vertices[5]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = 3.5
        with ref(n_nitrishapedata.vertices[6]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = 3.5
        with ref(n_nitrishapedata.vertices[7]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = 1.75
            
        n_nitrishapedata.has_normals = True
        n_nitrishapedata.normals.update_size()
        with ref(n_nitrishapedata.normals[0]) as n_vector3:
            n_vector3.x = 0.669057
            n_vector3.y = 0.4991
            n_vector3.z = -0.550676
        with ref(n_nitrishapedata.normals[1]) as n_vector3:
            n_vector3.x = 0.669057
            n_vector3.y = -0.4991
            n_vector3.z = -0.550676
        with ref(n_nitrishapedata.normals[2]) as n_vector3:
            n_vector3.x = -0.481826
            n_vector3.y = -0.64098
            n_vector3.z = -0.59743
        with ref(n_nitrishapedata.normals[3]) as n_vector3:
            n_vector3.x = -0.481826
            n_vector3.y = 0.64098
            n_vector3.z = -0.59743
        with ref(n_nitrishapedata.normals[4]) as n_vector3:
            n_vector3.x = 0.669057
            n_vector3.y = 0.4991
            n_vector3.z = 0.550676
        with ref(n_nitrishapedata.normals[5]) as n_vector3:
            n_vector3.x = -0.481826
            n_vector3.y = 0.64098
            n_vector3.z = 0.59743
        with ref(n_nitrishapedata.normals[6]) as n_vector3:
            n_vector3.x = -0.481826
            n_vector3.y = -0.64098
            n_vector3.z = 0.59743
        with ref(n_nitrishapedata.normals[7]) as n_vector3:
            n_vector3.x = 0.669027
            n_vector3.y = -0.4991
            n_vector3.z = 0.550676
            
        with ref(n_nitrishapedata.center) as n_vector3:
            n_vector3.x = 4.76837e-07
            n_vector3.y = 2.14577e-06
        
        n_nitrishapedata.radius = 11.1692
        n_nitrishapedata.consistency_flags = 16384
        n_nitrishapedata.num_triangles = 12
        n_nitrishapedata.num_triangle_points = 36
        n_nitrishapedata.has_triangles = True
        n_nitrishapedata.triangles.update_size()
        with ref(n_nitrishapedata.triangles[0]) as n_triangle:
            n_triangle.v_2 = 1
            n_triangle.v_3 = 2
        with ref(n_nitrishapedata.triangles[1]) as n_triangle:
            n_triangle.v_2 = 2
            n_triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[2]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 5
            n_triangle.v_3 = 6
        with ref(n_nitrishapedata.triangles[3]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 6
            n_triangle.v_3 = 7
        with ref(n_nitrishapedata.triangles[4]) as n_triangle:
            n_triangle.v_2 = 4
            n_triangle.v_3 = 7
        with ref(n_nitrishapedata.triangles[5]) as n_triangle:
            n_triangle.v_2 = 7
            n_triangle.v_3 = 1
        with ref(n_nitrishapedata.triangles[6]) as n_triangle:
            n_triangle.v_1 = 1
            n_triangle.v_2 = 7
            n_triangle.v_3 = 6
        with ref(n_nitrishapedata.triangles[7]) as n_triangle:
            n_triangle.v_1 = 1
            n_triangle.v_2 = 6
            n_triangle.v_3 = 2
        with ref(n_nitrishapedata.triangles[8]) as n_triangle:
            n_triangle.v_1 = 2
            n_triangle.v_2 = 6
            n_triangle.v_3 = 5
        with ref(n_nitrishapedata.triangles[9]) as n_triangle:
            n_triangle.v_1 = 2
            n_triangle.v_2 = 5
            n_triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[10]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[11]) as n_triangle:
            n_triangle.v_1 = 4
            n_triangle.v_2 = 3
            n_triangle.v_3 = 5
    return n_data

def n_check_trishape(n_trishape):
    nose.tools.assert_is_instance(n_trishape, NifFormat.NiTriShape)
    n_check_transform(n_trishape)
    n_check_trishape_data(n_trishape.data)

def n_check_transform(n_trishape):        
    nose.tools.assert_equal(n_trishape.translation.as_tuple(),(20.0, 20.0, 20.0)) # location
    
    n_rot_eul = mathutils.Matrix(n_trishape.rotation.as_tuple()).to_euler()
    nose.tools.assert_equal((n_rot_eul.x - math.radians(30.0)) < EPSILON, True) # x rotation
    nose.tools.assert_equal((n_rot_eul.y - math.radians(60.0)) < EPSILON, True) # y rotation
    nose.tools.assert_equal((n_rot_eul.z - math.radians(90.0)) < EPSILON, True) # z rotation
    
    nose.tools.assert_equal(n_trishape.scale - 0.75 < EPSILON, True) # scale

def n_check_trishape_data(n_trishape_data):
    nose.tools.assert_true(n_trishape_data.has_vertices)
    nose.tools.assert_equal(n_trishape_data.num_vertices, 8)
    nose.tools.assert_equal(n_trishape_data.num_triangles, 12)
    verts = {
        tuple(round(co, 4) for co in vert.as_list())
        for vert in n_trishape_data.vertices
        }
    nose.tools.assert_set_equal(verts, b_verts)
    
    #See Issue #26
    #nose.tools.assert_true(n_trishape_data.has_normals)
    #nose.tools.assert_equal(n_trishape_data.num_normals, 8)

    
    #TODO: Additional checks needed.
    
    #TriData
    #    Flags: blender - Continue, Maya - Triangles, Pyffi - Bound.
    #    Consistancy:
    #    radius:
