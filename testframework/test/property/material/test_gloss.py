"""Export and import material meshes."""

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

import bpy
import nose.tools

from pyffi.formats.nif import NifFormat

from test import SingleNif
from test.data import gen_data
from test.geometry.trishape import b_gen_geometry
from test.geometry.trishape import n_gen_geometry
from test.property.material import b_gen_material
from test.property.material import n_gen_material

class TestGlossProperty(SingleNif):
    """Export and import material meshes with gloss."""

    n_name = "property/material/test_gloss"
    b_name = 'Cube'

    def b_create_data(self):
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
        b_mat = b_gen_material.b_create_material_block(b_obj)      
        b_gen_material.b_create_set_default_material_property(b_mat)
        b_gen_material.b_create_gloss_property(b_mat) # set our gloss value

    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        b_mat = b_gen_material.b_check_material_block(b_obj)
        b_gen_material.b_check_gloss_property(b_mat)


    def n_create_data(self):
        gen_data.n_create_header(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_material.n_attach_material_prop(n_trishape)
        
        n_gen_material.n_alter_glossiness(n_trishape.properties[0])
        return self.n_data

    def n_check_data(self):
        n_nitrishape = self.n_data.roots[0].children[0]
        n_gen_geometry.n_check_trishape(n_nitrishape)

        # check we have property and correct type
        nose.tools.assert_equal(n_nitrishape.num_properties, 1)
        n_mat_prop = n_nitrishape.properties[0]        
        n_gen_material.n_check_material_block(n_mat_prop)
        
        # check its values
        n_gen_material.n_check_material_gloss_property(n_mat_prop)

    
