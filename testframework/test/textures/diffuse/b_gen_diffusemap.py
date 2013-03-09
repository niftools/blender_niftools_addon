from os import path

import bpy
import math
import mathutils

import nose

def b_create_diffuse_texture_properties(b_mat_texslot):
    '''Sets the textureslot settings for using a diffuse map'''
    
    b_mat_texslot.use_map_color_diffuse = True
    
    
def b_check_diffuse_texture_settings(b_mat_texslot):
    '''Test the textureslot for settings to use a diffusemap'''
    
    nose.tools.assert_equal(b_mat_texslot.use_map_color_diffuse, True)