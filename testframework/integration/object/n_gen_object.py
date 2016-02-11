"""Helper functions to create and test pyffi-based geometry blocks"""

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

import math
import mathutils

import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat


def n_create_blocks(n_data):
    n_ninode_1 = NifFormat.NiNode()
    n_ninode_2 = NifFormat.NiNode()
    n_data.roots = [n_ninode_1]

    with ref(n_ninode_1) as n_ninode:
        n_ninode.name = b'Scene Root'
        n_ninode.flags = 14
        with ref(n_ninode.rotation) as n_matrix33:
            n_matrix33.m_11 = 1
            n_matrix33.m_22 = 1
            n_matrix33.m_33 = 1
        n_ninode.scale = 1
        n_ninode.num_children = 1
        n_ninode.children.update_size()
        n_ninode.children[0] = n_ninode_2
        
        n_ninode_2.name = b'NifObject'
        n_ninode_2.flags = 14
        with ref(n_ninode_2.translation) as n_vector3:
            n_vector3.x = 20
            n_vector3.y = 20
            n_vector3.z = 20
        with ref(n_ninode_2.rotation) as n_matrix33:
            n_matrix33.m_11 = 0.0
            n_matrix33.m_21 = -0.5
            n_matrix33.m_31 = 0.866025
            n_matrix33.m_12 = 0.866025
            n_matrix33.m_22 = -0.433013
            n_matrix33.m_32 = -0.25
            n_matrix33.m_13 = 0.5
            n_matrix33.m_23 = 0.75
            n_matrix33.m_33 = 0.433012
            assert(n_matrix33.is_rotation()) # make sure in case we change values:
        n_ninode_2.scale = 0.75

    return n_data

def n_check_ninode(n_trishape):
    nose.tools.assert_is_instance(n_trishape, NifFormat.NiNode)
        

def n_check_transform(n_ninode):        
    nose.tools.assert_equal(n_ninode.translation.as_tuple(),(20.0, 20.0, 20.0)) # location
    
    n_rot_eul = mathutils.Matrix(n_ninode.rotation.as_tuple()).to_euler()
    nose.tools.assert_equal((n_rot_eul.x - math.radians(30.0)) < NifFormat.EPSILON, True) # x rotation
    nose.tools.assert_equal((n_rot_eul.y - math.radians(60.0)) < NifFormat.EPSILON, True) # y rotation
    nose.tools.assert_equal((n_rot_eul.z - math.radians(90.0)) < NifFormat.EPSILON, True) # z rotation
    
    nose.tools.assert_equal(n_ninode.scale - 0.75 < NifFormat.EPSILON, True) # scale
