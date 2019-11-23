
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

from os import path

import bpy

import nose


def b_create_textureslot(b_mat, b_text_name):
    """Creates a new empty textureslot and adds it to the provided Bpy.Types.Material"""
    
    b_mat_texslot = b_mat.texture_slots.add()  # create material texture slot
    b_mat_texslot.texture = bpy.data.textures.new(name=b_text_name, type='IMAGE')  # create texture holder
    return b_mat_texslot


def b_create_load_texture(b_mat_texslot, abs_text_path):
    """Loads a physical image file from disk and updates the textureslot's UV mapping to display it"""
    
    b_mat_texslot.texture.image = bpy.data.images.load(abs_text_path)
    b_mat_texslot.use = True
    b_mat_texslot.texture_coords = 'UV'
    b_mat_texslot.uv_layer = 'UVMap'
   
     
def b_check_texture_slot(b_mat_texslot):
    """Checks the settings on the the block"""
    
    nose.tools.assert_equal(b_mat_texslot.use, True)  # check slot enabled
    nose.tools.assert_equal(b_mat_texslot.texture_coords, 'UV')
    nose.tools.assert_equal(b_mat_texslot.uv_layer, 'UVMap')
    
    
def b_check_image_texture_property(b_mat_texslot, texture_path):
    """Checks that the relative path is correct"""

    nose.tools.assert_is_instance(b_mat_texslot.texture, bpy.types.ImageTexture)  # check we have a texture

    n_split_path = texture_path.split(path.sep)
    n_rel_path = n_split_path[len(n_split_path)-3:]  # get a path relative to \\textures folder
    
    b_split_path = b_mat_texslot.texture.image.filepath
    b_split_path = b_split_path.split(path.sep)  # see if nif loaded correct path
    b_rel_path = b_split_path[len(b_split_path)-3:]
    
    nose.tools.assert_equal(b_rel_path, n_rel_path)  # see if we have the right images

