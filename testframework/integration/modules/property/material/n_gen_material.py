
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

import nose

from pyffi.utils.withref import ref
from pyffi.formats.nif import NifFormat


def n_attach_material_prop(n_trishape):
    """Attaches a NiMaterialProperty to a NiTrishape block property's array at pos[0]"""
    
    n_nimaterialprop = NifFormat.NiMaterialProperty()
    n_nimaterialprop.name = b'Material'
   
    with ref(n_nimaterialprop.ambient_color) as n_color3:
        n_color3.r = 1.0
        n_color3.g = 1.0
        n_color3.b = 1.0
        
    with ref(n_nimaterialprop.diffuse_color) as n_color3:
        n_color3.r = 1.0
        n_color3.g = 1.0
        n_color3.b = 1.0
        
    with ref(n_nimaterialprop.emissive_color) as n_color3:
        n_color3.r = 0.0
        n_color3.g = 0.0
        n_color3.b = 0.0
        
    with ref(n_nimaterialprop.specular_color) as n_color3:
        n_color3.r = 0.0
        n_color3.g = 0.0
        n_color3.b = 0.0
    
    n_nimaterialprop.glossiness = 12.5  # default nif.xml - 0.0, blender - 12.5
    n_nimaterialprop.alpha = 1.0  # default nif.xml - 0.0
    
    # add property to top of list
    n_trishape.properties.reverse()
    n_trishape.num_properties += 1
    n_trishape.properties.update_size()
    n_trishape.properties[-1] = n_nimaterialprop
    n_trishape.properties.reverse()


def n_alter_glossiness(n_nimaterialprop):
    n_nimaterialprop.glossiness = 25.0


def n_alter_emissive(n_nimaterialprop):
    n_nimaterialprop.emissive_color.r = 0.5


def n_check_material_block(n_mat_prop):
    nose.tools.assert_is_instance(n_mat_prop, NifFormat.NiMaterialProperty)


def n_check_material_property(n_mat_prop):
    """Checks default values"""
    
    nose.tools.assert_equal((n_mat_prop.ambient_color.r,
                             n_mat_prop.ambient_color.g,
                             n_mat_prop.ambient_color.b), 
                            (1.0, 1.0, 1.0))

    nose.tools.assert_equal((n_mat_prop.diffuse_color.r,
                             n_mat_prop.diffuse_color.g,
                             n_mat_prop.diffuse_color.b), 
                            (1.0, 1.0, 1.0))
    
    nose.tools.assert_equal((n_mat_prop.specular_color.r,
                             n_mat_prop.specular_color.g,
                             n_mat_prop.specular_color.b), 
                            (0.0, 0.0, 0.0))
    
    nose.tools.assert_equal((n_mat_prop.emissive_color.r,
                             n_mat_prop.emissive_color.g,
                             n_mat_prop.emissive_color.b), 
                            (0.0, 0.0, 0.0))
    
    nose.tools.assert_equal(n_mat_prop.glossiness, 12.5)
    nose.tools.assert_equal(n_mat_prop.alpha, 1.0)


def n_check_material_gloss_property(n_mat_prop):
    nose.tools.assert_equal(n_mat_prop.glossiness, 25)  # n_gloss = 4/b_gloss


def n_check_material_emissive_property(n_mat_prop):
    nose.tools.assert_equal((n_mat_prop.emissive_color.r,
                             n_mat_prop.emissive_color.g,
                             n_mat_prop.emissive_color.b),
                            (0.5,0.0,0.0))
