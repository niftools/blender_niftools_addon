'''Helper funcitons to create and check bhkBoxShape based collisions'''

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat

def n_attach_bhkconvextransform(n_bhkshape):
    '''Attaches a bhkTransform shape to store transform information'''
    
    n_bhkconvextransformshape = NifFormat.bhkConvexTransformShape()
    n_bhkshape.shape = n_bhkconvextransformshape
    
    with ref(n_bhkconvextransformshape) as n_bhktransform:

        n_bhktransform.material = getattr(NifFormat.HavokMaterial, 'HAV_MAT_WOOD') # 9
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

def n_attach_bhkboxshape(n_bhkshape):
    
    n_bhkboxshape = NifFormat.bhkBoxShape()
    n_bhkshape.shape = n_bhkboxshape
    
    n_bhkboxshape.material = getattr(NifFormat.HavokMaterial, 'HAV_MAT_WOOD') # 9
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
    

def n_check_bhkboxshape_data(data):
    nose.tools.assert_is_instance(data.body, NifFormat.bhkRigidBody);
    nose.tools.assert_is_instance(data.body.shape.shape, NifFormat.bhkBoxShape);
    nose.tools.assert_equal(data.body.shape.material, 9);
