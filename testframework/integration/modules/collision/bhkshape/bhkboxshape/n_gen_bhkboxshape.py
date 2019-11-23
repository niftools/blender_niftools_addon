'''Helper funcitons to create and check bhkBoxShape based collisions'''

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

import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_update_bhkrigidbody(n_bhkrigidbody):
    
    n_bhkrigidbody.layer = NifFormat.OblivionLayer.OL_CLUTTER # 4
    n_bhkrigidbody.layer_copy = n_bhkrigidbody.layer
    n_bhkrigidbody.col_filter = 1
    n_bhkrigidbody.col_filter_copy = n_bhkrigidbody.col_filter
    n_bhkrigidbody.unknown_int_2 = 2084020722
    n_bhkrigidbody.unknown_3_ints.update_size()
    n_bhkrigidbody.unknown_byte = 0
    n_bhkrigidbody.unknown_2_shorts.update_size()
    n_bhkrigidbody.unknown_2_shorts[0] = 35899
    n_bhkrigidbody.unknown_2_shorts[1] = 16336
    n_bhkrigidbody.unknown_7_shorts.update_size()
    n_bhkrigidbody.unknown_7_shorts[1] = 21280
    n_bhkrigidbody.unknown_7_shorts[2] = 4581
    n_bhkrigidbody.unknown_7_shorts[3] = 62977
    n_bhkrigidbody.unknown_7_shorts[4] = 65535
    n_bhkrigidbody.unknown_7_shorts[5] = 44
    
    with ref(n_bhkrigidbody.inertia) as n_inertiamatrix:
        n_inertiamatrix.m_11 = 0.304209
        n_inertiamatrix.m_12 = 0.0631379
        n_inertiamatrix.m_13 = 0.0364526
        n_inertiamatrix.m_21 = 0.0631379
        n_inertiamatrix.m_22 = 0.356824
        n_inertiamatrix.m_23 = 0.0546789
        n_inertiamatrix.m_31 = 0.0364526
        n_inertiamatrix.m_32 = 0.0546789
        n_inertiamatrix.m_33 = 0.293686
        
    with ref(n_bhkrigidbody.center) as n_vector4:
        n_vector4.x = 2.85714
        n_vector4.y = 2.85714
        n_vector4.z = 2.85714
        
    n_bhkrigidbody.linear_damping = 0.1
    n_bhkrigidbody.angular_damping = 0.05
    n_bhkrigidbody.friction = 0.3
    n_bhkrigidbody.restitution = 0.3
    n_bhkrigidbody.max_angular_velocity = 31.4159
    n_bhkrigidbody.penetration_depth = 0.15
    n_bhkrigidbody.motion_system = NifFormat.MotionSystem.MO_SYS_BOX # 4
    n_bhkrigidbody.quality_type = NifFormat.MotionQuality.MO_QUAL_MOVING # 4

def n_check_bhkrigidbody_data(n_bhkrigidbody):
    
    nose.tools.assert_equal(n_bhkrigidbody.layer, NifFormat.OblivionLayer.OL_CLUTTER) # 4
    nose.tools.assert_equal(n_bhkrigidbody.layer, n_bhkrigidbody.layer_copy)
    nose.tools.assert_equal(n_bhkrigidbody.col_filter, 1)
    nose.tools.assert_equal(n_bhkrigidbody.col_filter, n_bhkrigidbody.col_filter_copy)
    nose.tools.assert_equal(n_bhkrigidbody.motion_system, NifFormat.MotionSystem.MO_SYS_BOX) # 4
    nose.tools.assert_equal(n_bhkrigidbody.quality_type, NifFormat.MotionQuality.MO_QUAL_MOVING) # 4

def n_attach_bhkconvextransform(n_bhkshape):
    '''Attaches a bhkTransform shape to store transform information'''
    
    n_bhkconvextransformshape = NifFormat.bhkConvexTransformShape()
    n_bhkshape.shape = n_bhkconvextransformshape
    
    with ref(n_bhkconvextransformshape) as n_bhktransform:

        n_bhktransform.material = NifFormat.HavokMaterial.HAV_MAT_WOOD # 9
        n_bhktransform.unknown_float_1 = 0.1
        n_bhktransform.unknown_8_bytes.update_size()
        n_bhktransform.unknown_8_bytes[0] = 96
        n_bhktransform.unknown_8_bytes[1] = 120
        n_bhktransform.unknown_8_bytes[2] = 53
        n_bhktransform.unknown_8_bytes[3] = 19
        n_bhktransform.unknown_8_bytes[4] = 24
        n_bhktransform.unknown_8_bytes[5] = 9
        n_bhktransform.unknown_8_bytes[6] = 253
        n_bhktransform.unknown_8_bytes[7] = 4
        
        with ref(n_bhktransform.transform) as n_matrix44:
            n_matrix44.m_11 = -2.23517e-08
            n_matrix44.m_21 = 0.649519
            n_matrix44.m_31 = 0.375
            n_matrix44.m_12 = -0.375
            n_matrix44.m_22 = -0.32476
            n_matrix44.m_32 = 0.5625
            n_matrix44.m_13 = 0.649519
            n_matrix44.m_23 = -0.1875
            n_matrix44.m_33 = 0.324759
            n_matrix44.m_14 = 2.85714
            n_matrix44.m_24 = 2.85714
            n_matrix44.m_34 = 2.85714
            
    return n_bhktransform


def n_check_bhkconvextransform_data(n_bhkrigidbody):
    nose.tools.assert_equal(n_bhkrigidbody.shape != None, True)
    n_bhktransform = n_bhkrigidbody.shape
    nose.tools.assert_is_instance(n_bhktransform, NifFormat.bhkConvexTransformShape)
    
    return n_bhktransform

def n_attach_bhkboxshape(n_bhkshape):
    
    n_bhkboxshape = NifFormat.bhkBoxShape()
    n_bhkshape.shape = n_bhkboxshape
    
    n_bhkboxshape.material = NifFormat.HavokMaterial.HAV_MAT_WOOD # 9    
    n_bhkboxshape.radius = 0.1
    n_bhkboxshape.unknown_8_bytes.update_size()
    n_bhkboxshape.unknown_8_bytes[0] = 107
    n_bhkboxshape.unknown_8_bytes[1] = 238
    n_bhkboxshape.unknown_8_bytes[2] = 67
    n_bhkboxshape.unknown_8_bytes[3] = 64
    n_bhkboxshape.unknown_8_bytes[4] = 58
    n_bhkboxshape.unknown_8_bytes[5] = 239
    n_bhkboxshape.unknown_8_bytes[6] = 142
    n_bhkboxshape.unknown_8_bytes[7] = 62
    with ref(n_bhkboxshape.dimensions) as n_vector3:
        n_vector3.x = 1.07143
        n_vector3.y = 1.07143
        n_vector3.z = 0.5
    n_bhkboxshape.minimum_size = 0.5    

def n_check_bhkboxshape_data(n_bhkconvextransfrom):
    nose.tools.assert_equal(n_bhkconvextransfrom.shape != None, True)
    n_bhkboxshape = n_bhkconvextransfrom.shape
    nose.tools.assert_is_instance(n_bhkboxshape, NifFormat.bhkBoxShape)
    
