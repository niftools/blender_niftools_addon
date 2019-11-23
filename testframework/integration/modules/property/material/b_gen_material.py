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
import nose


def b_create_material_block(b_obj):
    b_mat = bpy.data.materials.new(name='Material')
    b_obj.data.materials.append(b_mat)
    bpy.ops.object.shade_smooth()
    return b_mat


def b_create_set_default_material_property(b_mat):
    b_mat.diffuse_color = (1.0, 1.0, 1.0)  # default - (0.8, 0.8, 0.8)
    b_mat.diffuse_intensity = 1.0  # default - 0.8
    b_mat.specular_intensity = 0.0  # disable NiSpecularProperty
    return b_mat


def b_check_material_block(b_obj):
    """Check that we have a material"""

    b_mesh = b_obj.data
    b_mat = b_mesh.materials[0]
    nose.tools.assert_equal(len(b_mesh.materials), 1)
    return b_mat


def b_check_material_property(b_mat):
    """Check material has the correct properties"""

    nose.tools.assert_equal(b_mat.ambient, 1.0)
    nose.tools.assert_equal(b_mat.diffuse_color.r, 1.0)
    nose.tools.assert_equal(b_mat.diffuse_color.g, 1.0)
    nose.tools.assert_equal(b_mat.diffuse_color.b, 1.0)
    nose.tools.assert_equal(b_mat.specular_intensity, 0.0)


def b_create_gloss_property(b_mat):
    b_mat.specular_hardness = 100
    return b_mat


def b_check_gloss_property(b_mat):
    nose.tools.assert_equal(b_mat.specular_hardness, 100)


def b_create_emmisive_property(b_mat):
    b_mat.niftools.emissive_color = (0.5, 0.0, 0.0)
    b_mat.emit = 1.0
    return b_mat


def b_check_emission_property(b_mat):
    nose.tools.assert_equal(b_mat.emit, 1.0)
    nose.tools.assert_equal((b_mat.niftools.emissive_color.r,
                             b_mat.niftools.emissive_color.g,
                             b_mat.niftools.emissive_color.b),
                            (0.5, 0.0, 0.0))
