"""Common methods to related collision"""

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
import mathutils

import nose.tools

from pyffi.formats.nif import NifFormat

HAVOK_SCALE = 7

def b_create_default_collision_properties(b_col_obj):
    """Set the default properties for a collision object"""
    
    b_col_obj.draw_type = 'WIRE' # visual aid, no need to check
    b_col_obj.game.use_collision_bounds = True #also enables BGE visualisation
    b_col_obj.nifcollision.col_filter = 1
    

def b_check_default_collision_properties(b_col_obj):
    """Checks the default properties for a collision object"""
    
    nose.tools.assert_equal(b_col_obj.game.use_collision_bounds, True)
    nose.tools.assert_equal(b_col_obj.nifcollision.col_filter, 1)
    
    
def b_create_translation_matrix():
     #translation
    b_trans_mat = mathutils.Matrix.Translation((20.0, 20.0, 20.0))    
    return b_trans_mat

    
def b_check_translation_matrix(b_obj):
    """Checks that transation is (20,20,20)"""
    b_loc_vec = b_obj.matrix_local.decompose()[0] # transforms
    nose.tools.assert_equal(b_obj.location, mathutils.Vector((20.0, 20.0, 20.0))) # location
    


   
    
