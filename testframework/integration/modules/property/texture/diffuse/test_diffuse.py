"""Export and import textured meshes."""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005, NIF File Format Library and Tools contributors.
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
import os.path

from integration import SingleNif
from integration.modules.property import texture
from integration.modules.scene import n_gen_header, b_gen_header
from integration.modules.geometry.trishape import b_gen_geometry
from integration.modules.geometry.vertex.uv import b_gen_uv
from integration.modules.property.material import b_gen_material, n_gen_material
from integration.modules.property.texture import b_gen_texture, n_gen_texture
from integration.modules.property.texture.diffuse import b_gen_diffusemap, n_gen_diffusemap


class TestTexturePropertyDiffuseMap(SingleNif):
    """Test import/export of meshes with NiTexturingProperty based diffuse texture"""

    g_path = "property/texture"
    g_name = "test_diffuse"
    b_name = 'Cube'

    # Paths
    texture_dir = texture.TEXTURE_DATA_DIR

    diffuse_texture_path = os.path.join(texture_dir, 'diffuse', 'diffuse.dds')

    def b_create_header(self):
        b_gen_header.b_create_oblivion_info()

    def b_create_data(self):
        b_obj = b_gen_geometry.b_create_cube(self.b_name)
        b_gen_uv.b_uv_object()
        b_gen_geometry.b_transform_cube(b_obj)
        
        b_mat = b_gen_material.b_create_material_block(b_obj)
        b_gen_material.b_create_set_default_material_property(b_mat)
        
        b_texture_node = b_gen_texture.b_create_textureslot(b_mat, 'Diffuse')
        b_gen_texture.b_create_load_texture(b_texture_node, self.diffuse_texture_path)
        b_gen_diffusemap.b_create_diffuse_texture_properties(b_texture_node)
        
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        # TODO [geometry][uv] assertions should go in here.
        
        b_mat = b_gen_material.b_check_material_block(b_obj)  # check we have a material
        b_gen_material.b_check_material_property(b_mat)  # check its values
        
        nose.tools.assert_equal(b_mat.texture_slots[0] is not None, True)  # check slot exists
        b_texslot_diffuse = b_mat.texture_slots[0]
        b_gen_texture.b_check_texture_slot(b_texslot_diffuse)
        b_gen_texture.b_check_image_texture_property(b_texslot_diffuse, self.diffuse_texture_path)  
        b_gen_diffusemap.b_check_diffuse_texture_settings(b_texslot_diffuse)

    def n_create_header(self):
        n_gen_header.n_create_header_oblivion(self.n_data)

    def n_create_data(self):
        n_gen_texture.n_create_blocks(self.n_data)
        
        n_nitrishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_nitrishape)  # add nimaterialprop
        
        n_gen_texture.n_create_store_normal_data(n_nitrishape)  # store normal data as NiBinaryExtraData
        n_gen_texture.n_create_texture_property(n_nitrishape)  # add nitexturingprop
        
        n_textureprop = n_nitrishape.properties[0]
        n_gen_diffusemap.n_create_diffuse_map(n_textureprop, self.diffuse_texture_path)  # add nitexturesource diffuse

        return self.n_data

    def n_check_data(self):
        # TODO [geometry][uv] assertions should go in here.
        n_geom = self.n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2)  # mat & texture
        n_gen_material.n_check_material_property(n_geom.properties[1])
             
        n_tex_prop = n_geom.properties[0]
        n_gen_texture.n_check_texturing_property(n_tex_prop)  # check generic props
        n_gen_diffusemap.n_check_diffuse_property(n_tex_prop)  # check diffuse settings
        
        n_texdesc_diffuse = n_tex_prop.base_texture
        n_gen_texture.n_check_texdesc(n_texdesc_diffuse)  # check generic props
        n_gen_diffusemap.n_check_diffuse_source_texture(n_texdesc_diffuse.source, self.diffuse_texture_path)  # check diffuse image
