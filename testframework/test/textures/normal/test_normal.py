"""Export and import textured meshes."""

import bpy
import nose.tools
import os.path

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.geometry.uv import b_gen_uv
from test.geometry.uv import n_gen_uv
from test.property.material import b_gen_material
from test.property.material import n_gen_material
from test.textures import b_gen_texture
from test.textures import n_gen_texture
from test.textures.diffuse import b_gen_diffusemap
from test.textures.diffuse import n_gen_diffusemap
from test.textures.normal import b_gen_normalmap
from test.textures.normal import n_gen_normalmap

'''
Normal map, technically special case....
Handling if user supplies normal map instead of bump & vice-versa

    Extra_shader_data -> NormalMapIndex (Civ VI, Sid Miener)
    BSShaderPPLightingProperty (FO3 & NV)
    BSLightingShaderProperty(Skyrim)
'''

class TestTexturePropertyNormalMap(SingleNif):
    """Test import/export of meshes with NiTexturingProperty based diffuse texture"""
    
    n_name = "textures/diffuse/test_diffuse"
    b_name = 'Cube'

    # Paths
    root_dir = os.getcwd()
    nif_dir = os.path.join(root_dir, 'nif')
    
    diffuse_texture_path = os.path.join(nif_dir, 'textures', 'diffuse', 'diffuse.dds')
    normalmap_texture_path = os.path.join(nif_dir, 'textures', 'normal', 'normal.dds')
    
    def b_create_objects(self):
        b_obj = b_gen_geometry.b_create_cube(self.b_name)
        b_gen_uv.b_uv_object()
        b_gen_geometry.b_transform_cube(b_obj)
        
        b_mat = b_gen_material.b_create_material_block(b_obj)
        b_gen_material.b_create_set_default_material_property(b_mat)
        
        # diffuse
        b_mat_texslot = b_gen_texture.b_create_textureslot(b_mat, 'Diffuse')
        b_gen_texture.b_create_load_texture(b_mat_texslot, self.diffuse_texture_path)
        b_gen_diffusemap.b_create_diffuse_texture_properties(b_mat_texslot)
        
        # normal
        b_mat_texslot = b_gen_texture.b_create_textureslot(b_mat, 'normal')
        b_gen_texture.b_create_load_texture(b_mat_texslot, self.normalmap_texture_path)
        b_gen_normalmap.b_create_noraml_texture_properties(b_mat_texslot)
        

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        # TODO - probably should stick in some UV tests at some point.
        
        b_mat = b_gen_material.b_check_material_block(b_obj) # check we have a material
        b_gen_material.b_check_material_property(b_mat) # check its values
        
        # diffuse
        nose.tools.assert_equal(b_mat.texture_slots[0] != None, True) # check slot exists
        b_texslot_diffuse = b_mat.texture_slots[0]
        b_gen_texture.b_check_texture_slot(b_texslot_diffuse)
        b_gen_texture.b_check_image_texture_property(b_texslot_diffuse, self.diffuse_texture_path)  
        b_gen_diffusemap.b_check_diffuse_texture_settings(b_texslot_diffuse)
        
        # normal
        nose.tools.assert_equal(b_mat.texture_slots[1] != None, True) # check slot exists
        b_texslot_normal = b_mat.texture_slots[1]
        b_gen_texture.b_check_texture_slot(b_texslot_normal)
        b_gen_texture.b_check_image_texture_property(b_texslot_normal, self.normalmap_texture_path)  
        b_gen_normalmap.b_check_normal_texture_settings(b_texslot_normal)
        
        
    def n_create_data(self):
        
        gen_data.n_create_header(self.n_data)
        n_gen_texture.n_create_blocks(self.n_data)
        
        n_nitrishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_nitrishape) # add nimaterialprop
        
        n_gen_texture.n_create_store_normal_data(n_nitrishape) #store normal data as NiBinaryExtraData
        n_gen_texture.n_create_texture_property(n_nitrishape) # add nitexturingprop
        
        n_textureprop = n_nitrishape.properties[0]
        n_gen_diffusemap.n_create_diffuse_map(n_textureprop) #add nitexturesource diffuse
        n_gen_normalmap.n_create_normal_map(n_textureprop) #add nitexturesource normalmap
        
        return self.n_data


    def n_check_data(self):
        
        'TODO - probably should stick in some UV tests at some point.'
        n_geom = self.n_data.roots[0].children[0]
        nose.tools.assert_equal(n_geom.num_properties, 2) # mat & texture
        n_gen_material.n_check_material_property(n_geom.properties[1])
              
        n_tex_prop = n_geom.properties[0]
        n_gen_texture.n_check_texturing_property(n_tex_prop) #check generic props
        n_gen_diffusemap.n_check_diffuse_property(n_tex_prop) #check diffuse settings
        n_gen_normalmap.n_check_normal_property(n_tex_prop) #check normal settings
        
        # diffuse
        n_texdesc_diffuse = n_tex_prop.base_texture
        n_gen_texture.n_check_texdesc(n_texdesc_diffuse) # check generic props
        n_gen_diffusemap.n_check_diffuse_source_texture(n_texdesc_diffuse.source, self.diffuse_texture_path) #check diffuse image
        
        # normal
        n_texdesc_normalmap = n_tex_prop.normal_texture
        n_gen_texture.n_check_texdesc(n_texdesc_normalmap) # check generic props
        n_gen_normalmap.n_check_normal_map_source_texture(n_texdesc_normalmap.source, self.normalmap_texture_path) #check diffuse image
 

    def n_check_texturing_property(self, n_tex_prop):
        nose.tools.assert_is_instance(n_tex_prop, NifFormat.NiTexturingProperty)
        nose.tools.assert_equal(n_tex_prop.has_, True)
        self.n_check_base_texture(n_tex_prop.base_texture)

'''
