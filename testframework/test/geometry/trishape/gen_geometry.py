from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_create():
    n_ninode_1 = NifFormat.NiNode()
    n_nitrishape_1 = NifFormat.NiTriShape()
    n_nitrishapedata_1 = NifFormat.NiTriShapeData()
    n_data = NifFormat.Data()
    n_data.roots = [n_ninode_1]
    n_data.version = 0x14000005
    n_data.user_version = 11
    n_data.user_version_2 = 11

    with ref(n_ninode_1) as n_ninode:
        n_ninode.name = b'Scene Root'
        n_ninode.flags = 14
        with ref(n_ninode.rotation) as rotation:
            rotation.m_11 = 1.0
            rotation.m_22 = 1.0
            rotation.m_33 = 1.0
        n_ninode.scale = 1.0
        n_ninode.num_children = 1
        n_ninode.children.update_size()
        n_ninode.children[0] = n_nitrishape_1

    with ref(n_nitrishape_1) as n_nitrishape:
        n_nitrishape.name = b'Cube'
        n_nitrishape.flags = 14
        with ref(n_nitrishape.translation) as translation:
            translation.x = 20.0
            translation.y = 20.0
            translation.z = 20.0
        with ref(n_nitrishape.rotation) as rotation:
            rotation.m_11 = 0
            rotation.m_21 = -0.5
            rotation.m_31 = 0.866025447845459
            rotation.m_12 = 0.8660253882408142
            rotation.m_22 = -0.4330127537250519
            rotation.m_32 = -0.25
            rotation.m_13 = 0.5
            rotation.m_23 = 0.75
            rotation.m_33 = 0.4330126643180847
        n_nitrishape.scale = 0.75
        n_nitrishape.data = n_nitrishapedata_1

    with ref(n_nitrishapedata_1) as n_nitrishapedata:
        n_nitrishapedata.num_vertices = 8
        n_nitrishapedata.has_vertices = True
        n_nitrishapedata.vertices.update_size()
        with ref(n_nitrishapedata.vertices[0]) as vertex:
            vertex.x = 7.5
            vertex.y = 3.75
            vertex.z = -1.875
        with ref(n_nitrishapedata.vertices[1]) as vertex:
            vertex.x = 7.5
            vertex.y = -3.75
            vertex.z = -1.875
        with ref(n_nitrishapedata.vertices[2]) as vertex:
            vertex.x = -7.5
            vertex.y = -7.5
            vertex.z = -3.75
        with ref(n_nitrishapedata.vertices[3]) as vertex:
            vertex.x = -7.5
            vertex.y = 7.5
            vertex.z = -3.75
        with ref(n_nitrishapedata.vertices[4]) as vertex:
            vertex.x = 7.5
            vertex.y = 3.75
            vertex.z = 1.875
        with ref(n_nitrishapedata.vertices[5]) as vertex:
            vertex.x = -7.5
            vertex.y = 7.5
            vertex.z = 3.75
        with ref(n_nitrishapedata.vertices[6]) as vertex:
            vertex.x = -7.5
            vertex.y = -7.5
            vertex.z = 3.75
        with ref(n_nitrishapedata.vertices[7]) as vertex:
            vertex.x = 7.5
            vertex.y = -3.75
            vertex.z = 1.875

        n_nitrishapedata.radius = 11.25
        n_nitrishapedata.consistency_flags = 16384

        n_nitrishapedata.num_triangles = 12
        n_nitrishapedata.num_triangle_points = 36
        n_nitrishapedata.has_triangles = True
        n_nitrishapedata.triangles.update_size()

        with ref(n_nitrishapedata.triangles[0]) as triangle:
            triangle.v_2 = 1
            triangle.v_3 = 2
        with ref(n_nitrishapedata.triangles[1]) as triangle:
            triangle.v_2 = 2
            triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[2]) as triangle:
            triangle.v_1 = 4
            triangle.v_2 = 5
            triangle.v_3 = 6
        with ref(n_nitrishapedata.triangles[3]) as triangle:
            triangle.v_1 = 4
            triangle.v_2 = 6
            triangle.v_3 = 7
        with ref(n_nitrishapedata.triangles[4]) as triangle:
            triangle.v_2 = 4
            triangle.v_3 = 7
        with ref(n_nitrishapedata.triangles[5]) as triangle:
            triangle.v_2 = 7
            triangle.v_3 = 1
        with ref(n_nitrishapedata.triangles[6]) as triangle:
            triangle.v_1 = 1
            triangle.v_2 = 7
            triangle.v_3 = 6
        with ref(n_nitrishapedata.triangles[7]) as triangle:
            triangle.v_1 = 1
            triangle.v_2 = 6
            triangle.v_3 = 2
        with ref(n_nitrishapedata.triangles[8]) as triangle:
            triangle.v_1 = 2
            triangle.v_2 = 6
            triangle.v_3 = 5
        with ref(n_nitrishapedata.triangles[9]) as triangle:
            triangle.v_1 = 2
            triangle.v_2 = 5
            triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[10]) as triangle:
            triangle.v_1 = 4
            triangle.v_3 = 3
        with ref(n_nitrishapedata.triangles[11]) as triangle:
            triangle.v_1 = 4
            triangle.v_2 = 3
            triangle.v_3 = 5

        n_nitrishapedata.has_normals = True
        n_nitrishapedata.normals.update_size()
        with ref(n_nitrishapedata.normals[0]) as normal:
            normal.x = 0.6712851524353027
            normal.y = 0.4993438422679901
            normal.z = -0.5477156639099121
        with ref(n_nitrishapedata.normals[1]) as normal:
            normal.x = 0.6712851524353027
            normal.y = -0.4993438422679901
            normal.z = -0.5477156639099121
        with ref(n_nitrishapedata.normals[2]) as normal:
            normal.x = -0.47993406653404236
            normal.y = -0.6403393745422363
            normal.z = -0.599627673625946
        with ref(n_nitrishapedata.normals[3]) as normal:
            normal.x = -0.47993406653404236
            normal.y = 0.6403393745422363
            normal.z = -0.599627673625946
        with ref(n_nitrishapedata.normals[4]) as normal:
            normal.x = 0.6712851524353027
            normal.y = 0.4993438422679901
            normal.z = 0.5477156639099121
        with ref(n_nitrishapedata.normals[5]) as normal:
            normal.x = -0.47993406653404236
            normal.y = 0.6403393745422363
            normal.z = 0.599627673625946
        with ref(n_nitrishapedata.normals[6]) as normal:
            normal.x = -0.47993406653404236
            normal.y = -0.6403393745422363
            normal.z = 0.599627673625946
        with ref(n_nitrishapedata.normals[7]) as normal:
            normal.x = 0.6712851524353027
            normal.y = -0.4993438422679901
            normal.z = 0.5477156639099121

    return n_data
