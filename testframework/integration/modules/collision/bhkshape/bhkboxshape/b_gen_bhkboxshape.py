"""Methods to test bhkboxshape."""

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

def b_create_bhkboxshape_properties(b_col_obj):
    """Set the object to be Box Collision."""
    
    b_col_obj.nifcollision.oblivion_layer = "OL_CLUTTER" # 4
    b_col_obj.nifcollision.motion_system = "MO_SYS_BOX" # 4
    b_col_obj.nifcollision.quality_type = "MO_QUAL_MOVING" # 4
    
    b_col_obj.game.collision_bounds_type = 'BOX'
    b_col_obj.nifcollision.havok_material = "HAV_MAT_WOOD" # 9
    
    
def b_check_bhkboxshape_properties(b_col_obj):
    """Check the box collision related property."""
    #bhkrigidbody
    nose.tools.assert_equal(b_col_obj.nifcollision.oblivion_layer, "OL_CLUTTER") # 4
    nose.tools.assert_equal(b_col_obj.nifcollision.motion_system, "MO_SYS_BOX") # 4
    nose.tools.assert_equal(b_col_obj.nifcollision.quality_type , "MO_QUAL_MOVING") # 4
    
    #bhkshape
    nose.tools.assert_equal(b_col_obj.game.collision_bounds_type, 'BOX')
    nose.tools.assert_equal(b_col_obj.nifcollision.havok_material, "HAV_MAT_WOOD") # 9
