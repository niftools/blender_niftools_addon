"""Exports and imports vertex color"""

import bpy
import nose.tools

from integration import SingleNif
from integration.data import n_gen_header, b_gen_header
from integration.modules.geometry.trishape import n_gen_geometry, b_gen_geometry
from integration.modules.geometry.vertex.color import n_gen_vertexcolor


class TestBaseVertexColor(SingleNif):

    b_name = "Cube"
    g_path = "geometry/vertex"
    g_name = "test_vertex_color"

    def b_create_header(self):
        b_gen_header.b_create_oblivion_info()

    def n_create_header(self):
        n_gen_header.n_create_header_oblivion(self.n_data)

    # vertex color specific stuff
    b_faces = [(4, 0, 3),  # 0
               (4, 3, 7),  # 1
               (2, 6, 7),  # 2
               (2, 7, 3),  # 3
               (1, 5, 2),  # 4
               (5, 6, 2),  # 5
               (0, 4, 1),  # 6
               (4, 5, 1),  # 7
               (4, 7, 5),  # 8
               (7, 6, 5),  # 9
               (0, 1, 2),  # 10
               (0, 2, 3)]  # 11

    # nif mapping to base, might be useful
    n_faces = [(0, 1, 2),
               (0, 2, 3),
               (4, 5, 6),
               (4, 6, 7),
               (0, 4, 7),
               (0, 7, 1),
               (1, 7, 6),
               (1, 6, 2),
               (2, 6, 5),
               (2, 5, 3),
               (4, 0, 3),
               (4, 3, 5)]

    vertcol = [(1.0, 0.0, 0.0),  # R
               (0.0, 1.0, 0.0),  # G
               (0.0, 0.0, 1.0),  # B
               (0.0, 0.0, 0.0),  # A
               (1.0, 0.0, 0.0),  # R
               (0.0, 1.0, 0.0),  # G
               (0.0, 0.0, 1.0),  # B
               (0.0, 0.0, 0.0)]  # A

    def b_create_data(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        self.b_create_vertexcolor(b_obj)

    def b_create_vertexcolor(self, b_obj):
        """Create vertex colors"""

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.object.editmode_toggle()

        # add base vertex color layer
        print(len(b_obj.data.vertex_colors))
        bpy.ops.mesh.vertex_color_add()
        b_obj.data.vertex_colors[0].name = "VertexColor"
        print(len(b_obj.data.vertex_colors))

        # iterate over each face, then set the vert color through lookup
        # TODO use vertex coordinate to map vertex color
        #      (we should not rely on vertex ordering)
        for face_index, face in enumerate(self.b_faces):  # nif_faces: 0-11
            for vert_index, n_vert in enumerate(face):  # nif_verts: 0-7
                b_meshcolor = b_obj.data.vertex_colors["VertexColor"].data[face_index]
                b_color = getattr(b_meshcolor, "color%s" % (vert_index + 1))
                b_color.r = self.vertcol[n_vert][0]
                b_color.g = self.vertcol[n_vert][1]
                b_color.b = self.vertcol[n_vert][2]

    def b_check_data(self):
        # TODO nif file has wrong transform and wrong geometry
        # TestBaseGeometry.b_check_data(self)
        b_obj = bpy.data.objects[self.b_name]
        b_mesh = b_obj.data
        self.b_check_vertex_layers(b_mesh)

    def b_check_vertex_layers(self, b_mesh):
        # TODO fix, length is 2 during one of the checks
        # nose.tools.assert_equal(len(b_mesh.vertex_colors), 1)
        nose.tools.assert_equal(b_mesh.vertex_colors[0].name, 'VertexColor')
        b_meshcolor = b_mesh.vertex_colors["VertexColor"].data
        for b_col_index, b_meshcolor in enumerate(b_meshcolor):
            self.b_check_vert_colors(b_col_index, b_meshcolor)

    def b_check_vert_colors(self, f_index, vertexcolor):
        for vert_index in [0, 1, 2]:
            b_color = getattr(vertexcolor, "color%s" % (vert_index + 1))
            # TODO fix
            # nose.tools.assert_almost_equal(b_color.r, self.vertcol[f_index][0])
            # nose.tools.assert_almost_equal(b_color.g, self.vertcol[f_index][1])
            # nose.tools.assert_almost_equal(b_color.b, self.vertcol[f_index][2])

    def n_create_data(self):
        n_gen_geometry.n_create_blocks(self.n_data)

        n_nitrishapedata = self.n_data.roots[0].children[0].data
        self.n_data.roots[0].children[0].data = n_gen_vertexcolor.n_add_vertex_colors(n_nitrishapedata)

    def n_check_data(self):
        # TODO nif file has wrong transform and wrong geometry
        # TestBaseGeometry.n_check_data(self, n_data)
        n_geom = self.n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.data.has_vertex_colors, True)
        # TODO vertex split due to multiple vcols per vertex?
        #      fix this in data
        # nose.tools.assert_equal(len(n_geom.data.vertex_colors), 8)
        for i, vert in enumerate(n_geom.data.vertex_colors):
            self.n_check_vert(i, vert)

    def n_check_vert(self, index, vertexcolor):
        pass
        # TODO fix
        # print("Sub Check: Comparing vertex color")
        # print("n_vert:" + str(vertexcolor.r) + " base_vert:" + str(self.vertcol[index][0]))
        # nose.tools.assert_equal(abs(vertexcolor.r - self.vertcol[index][0]) > 0.01, False)
        # print("n_vert:" + str(vertexcolor.g) + " base_vert:" + str(self.vertcol[index][1]))
        # nose.tools.assert_equal(abs(vertexcolor.g - self.vertcol[index][1]) > 0.01, False)
        # print("n_vert:" + str(vertexcolor.b) + " base_vert:" + str(self.vertcol[index][2]))
        # nose.tools.assert_equal(abs(vertexcolor.b - self.vertcol[index][2]) > 0.01, False)
