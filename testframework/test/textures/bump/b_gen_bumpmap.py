from os import path

import bpy
import math
import mathutils

import nose

def b_create_bumpmap_texture_properties(b_mat_texslot):
    #Influence mapping
    b_mat_texslot.use_map_color_diffuse = False #auto-set on creation
    b_mat_texslot.texture.use_normal_map = False #causes artifacts, bumpmap is actually a heighmap.

    #Influence
    b_mat_texslot.use_map_normal = True
    
    
def b_check_bumpmap_texture_settings(b_mat_texslot):
    
    
    nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, False)
    nose.tools.assert_equal(b_mat_texslot.texture.use_normal_map, False)
    
    nose.tools.assert_equal(b_mat_texslot.use_map_normal, True)