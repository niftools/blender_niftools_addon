"""Methods to test bhkboxshape."""

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

def b_create_bhksphere(b_obj, b_name):
    """Create a UV Sphere encapsulating the given object"""
    
    #this assumes that the objects center is at the vertex mesh centre.
    b_obj_matrix = b_obj.matrix_local
    b_rot_quat = b_obj_matrix.decompose()[1]
    b_vertlist = [b_rot_quat * b_vert.co for b_vert in b_obj.data.vertices] #pre-compute where the vertices in local space
    
    minx = min([b_vert[0] for b_vert in b_vertlist])
    miny = min([b_vert[1] for b_vert in b_vertlist])
    minz = min([b_vert[2] for b_vert in b_vertlist])
    maxx = max([b_vert[0] for b_vert in b_vertlist])
    maxy = max([b_vert[1] for b_vert in b_vertlist])
    maxz = max([b_vert[2] for b_vert in b_vertlist])
    
    b_radius = max([abs(minx), abs(miny), abs(minz), abs(maxx), abs(maxy), abs(maxz)])
    
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16, size=b_radius)
    b_sphere_obj = b_obj = bpy.context.scene.objects.active
    b_sphere_obj.name = b_name
    b_sphere_obj.matrix_local = b_obj_matrix
        
    return b_sphere_obj


def b_create_bhksphereshape_properties(b_col_obj):
    """Set the object to be Sphere Collision."""
    
    b_col_obj.nifcollision.oblivion_layer = "OL_CLUTTER" # 4
    b_col_obj.nifcollision.motion_system = "MO_SYS_BOX" # 4
    b_col_obj.nifcollision.quality_type = "MO_QUAL_MOVING" # 4
    
    b_col_obj.game.collision_bounds_type = 'SPHERE'
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