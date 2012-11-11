from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat


def n_create_data():
    n_data = NifFormat.Data()
    n_data.version = 0x14000005
    n_data.user_version = 11
    n_data.user_version_2 = 11
    n_create_blocks(n_data)
    return n_data

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
            n_matrix33.m_11 = 0.433013
            n_matrix33.m_21 = -0.25
            n_matrix33.m_31 = 0.866025
            n_matrix33.m_12 = 0.808013
            n_matrix33.m_22 = 0.533494
            n_matrix33.m_32 = -0.25
            n_matrix33.m_13 = -0.399519
            n_matrix33.m_23 = 0.808013
            n_matrix33.m_33 = 0.433013
        n_nitrishape.scale = 0.75
        n_nitrishape.data = n_nitrishapedata_1
    with ref(n_nitrishapedata_1) as n_nitrishapedata:
        n_nitrishapedata.num_vertices = 8
        n_nitrishapedata.has_vertices = True
        n_nitrishapedata.vertices.update_size()
        with ref(n_nitrishapedata.vertices[0]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = -1.875
        with ref(n_nitrishapedata.vertices[1]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = -1.875
        with ref(n_nitrishapedata.vertices[2]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = -3.75
        with ref(n_nitrishapedata.vertices[3]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = -3.75
        with ref(n_nitrishapedata.vertices[4]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = 3.75
            n_vector3.z = 1.875
        with ref(n_nitrishapedata.vertices[5]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = 7.5
            n_vector3.z = 3.75
        with ref(n_nitrishapedata.vertices[6]) as n_vector3:
            n_vector3.x = -7.5
            n_vector3.y = -7.5
            n_vector3.z = 3.75
        with ref(n_nitrishapedata.vertices[7]) as n_vector3:
            n_vector3.x = 7.5
            n_vector3.y = -3.75
            n_vector3.z = 1.875
        n_nitrishapedata.has_normals = True
        n_nitrishapedata.normals.update_size()
        with ref(n_nitrishapedata.normals[0]) as n_vector3:
            n_vector3.x = 0.671285
            n_vector3.y = 0.499344
            n_vector3.z = -0.547716
        with ref(n_nitrishapedata.normals[1]) as n_vector3:
            n_vector3.x = 0.671285
            n_vector3.y = -0.499344
            n_vector3.z = -0.547716
        with ref(n_nitrishapedata.normals[2]) as n_vector3:
            n_vector3.x = -0.479934
            n_vector3.y = -0.640339
            n_vector3.z = -0.599628
        with ref(n_nitrishapedata.normals[3]) as n_vector3:
            n_vector3.x = -0.479934
            n_vector3.y = 0.640339
            n_vector3.z = -0.599628
        with ref(n_nitrishapedata.normals[4]) as n_vector3:
            n_vector3.x = 0.671285
            n_vector3.y = 0.499344
            n_vector3.z = 0.547716
        with ref(n_nitrishapedata.normals[5]) as n_vector3:
            n_vector3.x = -0.479934
            n_vector3.y = 0.640339
            n_vector3.z = 0.599628
        with ref(n_nitrishapedata.normals[6]) as n_vector3:
            n_vector3.x = -0.479934
            n_vector3.y = -0.640339
            n_vector3.z = 0.599628
        with ref(n_nitrishapedata.normals[7]) as n_vector3:
            n_vector3.x = 0.671285
            n_vector3.y = -0.499344
            n_vector3.z = 0.547716
        n_nitrishapedata.radius = 11.25
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
