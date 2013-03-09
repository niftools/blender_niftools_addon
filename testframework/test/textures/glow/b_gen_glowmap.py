from os import path

import bpy
import math
import mathutils

import nose

def b_create_glow_texture_properties(b_mat_texslot):
    '''Sets the textureslot settings for using a glow map'''
    
    #Influence mapping
    b_mat_texslot.use_map_color_diffuse = False
    b_mat_texslot.texture.use_alpha = False #If no alpha channel or white causes display error

    #Influence
    b_mat_texslot.use_map_emit = True
    
    
def b_check_glow_texture_settings(b_mat_texslot):
    '''Test the textureslot for settings to use a glow map'''
    
    nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, False)
    nose.tools.assert_equal(b_mat_texslot.texture.use_alpha, False)


    nose.tools.assert_equal(b_mat_texslot.use_map_emit, True)