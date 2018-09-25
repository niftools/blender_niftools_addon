"""Export and import meshes with material."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
# 
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
# 
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import bpy
import nose.tools

from integration import SingleNif
from integration.data import n_gen_header, b_gen_header
from integration.modules.geometry.trishape import b_gen_geometry, n_gen_geometry
from integration.modules.property.material import b_gen_material, n_gen_material


class TestMaterialProperty(SingleNif):
    """Test material property"""

    g_path = 'property/material'
    g_name = 'test_material'
    b_name = 'Cube'

    def b_create_header(self):
        b_gen_header.b_create_oblivion_info()

    def n_create_header(self):
        n_gen_header.n_create_header_oblivion(self.n_data)

    def b_create_data(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        b_mat = b_gen_material.b_create_material_block(b_obj)
        b_gen_material.b_create_set_default_material_property(b_mat)

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        b_mat = b_gen_material.b_check_material_block(b_obj)  # check we have a material
        b_gen_material.b_check_material_property(b_mat)  # check its values

    def n_create_data(self):
        n_gen_geometry.n_create_blocks(self.n_data)
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_trishape)  # add nimaterialprop

    def n_check_data(self):
        n_nitrishape = self.n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)

        nose.tools.assert_equal(n_nitrishape.num_properties, 1)
        n_mat_prop = n_nitrishape.properties[0]
        n_gen_material.n_check_material_block(n_mat_prop)
        n_gen_material.n_check_material_property(n_mat_prop)


'''
class TestAmbientMaterial(TestMaterialProperty):
    n_name = "property/material/base_ambient"

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_mat = b_obj.data.materials[0]

        #diffuse settings
        b_mat.niftools.ambient_color = (0.0,1.0,0.0)#TODO_3.0 - update func-> World ambient
        return b_obj

    def b_check_data(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_ambient_property(b_mat)

    def b_check_ambient_property(self, b_mat)
        nose.tools.assert_equal(b_mat.niftools.ambient_color, (0.0,1.0,0.0))

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        nose.tools.assert_equal(n_mat_prop.ambient_color, (0.0,1.0,0.0))

class TestDiffuseMaterial(TestMaterialProperty):
    n_name = "property/material/base_diffuse"

    def b_create_object(self):
        b_obj = TestBaseGeometry.b_create_object(self)
        b_mat = b_obj.data.materials[0]

        #diffuse settings
        b_mat.niftools.diffuse_color = (0.0,1.0,0.0)#TODO_3.0 - update func-> World ambient
        return b_obj

    def b_check_data(self, b_obj):
        b_mesh = b_obj.data
        b_mat = b_mesh.materials[0]
        self.b_check_diffuse_property(b_mat)

    def b_check_diffuse_property(self, b_mat)
        nose.tools.assert_equal(b_mat.niftools.diffuse_color, (0.0,1.0,0.0))
        nose.tools.assert_equal(b_mat.diffuse_intensity, 1.0)

    def n_check_data(self, n_data):
        n_geom = n_data.roots[0].children[0]
        self.n_check_material_property(n_geom.properties[0])

    def n_check_material_property(self, n_mat_prop):
        nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)
        nose.tools.assert_equal(n_mat_prop.diffuse_color, (0.0,1.0,0.0))

'''
