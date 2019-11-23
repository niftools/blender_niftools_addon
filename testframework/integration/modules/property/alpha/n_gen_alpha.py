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

from pyffi.formats.nif import NifFormat


def n_attach_alpha_prop(n_trishapedata):
    """Attaches a NiMaterialProperty to a trishapedata block property's array at pos[0]"""

    n_alphaprop = NifFormat.NiAlphaProperty()
    n_alphaprop.flags = 4845  # default = 237, see below
    n_alphaprop.threshold = 0  # Threshold for alpha testing (see: glAlphaFunc)

    # add property to top of list
    n_trishapedata.properties.reverse()

    n_trishapedata.num_properties += 1
    n_trishapedata.properties.update_size()
    n_trishapedata.properties[-1] = n_alphaprop

    n_trishapedata.properties.reverse()


''' Alpha flags bit values - 

    Bit 0 : alpha blending 
    enableBits 1-4 : source blend (glBlendFunc)
    modeBits 5-8 : destination blend (glBlendFunc)
    modeBit 9 : alpha test 
    enableBit 10-12 : alpha test (glAlphaFunc)
    modeBit 13 : no sorter flag ( disables triangle sorting )
        
    blend modes (glBlendFunc):
        0000 GL_ONE
        0001 GL_ZERO
        0010 GL_SRC_COLOR
        0011 GL_ONE_MINUS_SRC_COLOR
        0100 GL_DST_COLOR
        0101 GL_ONE_MINUS_DST_COLOR
        0110 GL_SRC_ALPHA
        0111 GL_ONE_MINUS_SRC_ALPHA
        1000 GL_DST_ALPHA
        1001 GL_ONE_MINUS_DST_ALPHA
        1010 GL_SRC_ALPHA_SATURATE
        
   test modes (glAlphaFunc):
       000 GL_ALWAYS
       001 GL_LESS
       010 GL_EQUAL
       011 GL_LEQUAL
       100 GL_GREATER
       101 GL_NOTEQUAL
       110 GL_GEQUAL
       111 GL_NEVER
'''


def n_alter_material_alpha(n_nimaterialprop):
    n_nimaterialprop.alpha = 0.5


def n_check_material_alpha(n_mat_prop):
    """Check that material has correct alpha value"""
    nose.tools.assert_equal(n_mat_prop.alpha, 0.5)


def n_check_alpha_block(n_alpha_prop):
    """Check that block is actually NiAlphaProperty"""
    nose.tools.assert_is_instance(n_alpha_prop, NifFormat.NiAlphaProperty)


def n_check_alpha_property(n_alpha_prop):
    """Check NiAlphaProperty values"""
    nose.tools.assert_equal(n_alpha_prop.flags, 4845)  # Ref: gen_alpha for values
    nose.tools.assert_equal(n_alpha_prop.threshold, 0)
