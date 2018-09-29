"""Export and import meshes with material."""

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
import math
import mathutils
import nose.tools

from pyffi.formats.nif import NifFormat

from integration import SingleNif
from integration.data import gen_data
from integration.geometry.trishape import b_gen_geometry
from integration.geometry.trishape import n_gen_geometry
from integration.collisions.bhkshape import b_gen_collision
from integration.collisions.bhkshape import n_gen_collision
from integration.collisions.bhkshape.bhksphereshape import b_gen_bhksphereshape
from integration.collisions.bhkshape.bhksphereshape import n_gen_bhksphereshape

class TestCollisionBhkSphereShape(SingleNif):
    """Test material property"""
    
    g_name = 'collisions/bhksphereshape/test_sphereshape'
    b_name = 'Cube'
    b_col_name = 'box'

    def b_create_data(self):
        '''Create a cube and bhksphereshape collision object'''
        
        #Mesh obj
        b_obj = b_gen_geometry.b_create_base_geometry(self.b_name)
                
        #Col obj
        b_col_obj = b_gen_bhksphereshape.b_create_bhksphere(b_obj, self.b_col_name)
        b_gen_collision.b_create_default_collision_properties(b_col_obj)
        b_gen_bhksphereshape.b_create_bhksphereshape_properties(b_col_obj)
        
        
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_geometry.b_check_geom_obj(b_obj)
        
        b_col_obj = bpy.data.objects[self.b_col_name]
        b_gen_collision.b_check_default_collision_properties(b_col_obj)
        b_gen_bhkboxshape.b_check_bhkboxshape_properties(b_col_obj)
    
    
    def n_create_data(self):
        gen_data.n_create_header_oblivion(self.n_data)
        n_gen_geometry.n_create_blocks(self.n_data)
        
        n_ninode = self.n_data.roots[0]
        n_gen_collision.n_attach_bsx_flag(n_ninode)
        
        #generate common collision tree
        n_bhkcolobj = n_gen_collision.n_attach_bhkcollisionobject(n_ninode)
        n_bhkrigidbody = n_gen_collision.n_attach_bhkrigidbody(n_bhkcolobj)
        
        #generate bhkboxshape specific data
        n_gen_bhkboxshape.n_update_bhkrigidbody(n_bhkrigidbody)
        n_bhktransform = n_gen_bhkboxshape.n_attach_bhkconvextransform(n_bhkrigidbody)
        n_gen_bhkboxshape.n_attach_bhkboxshape(n_bhktransform)
        
        return self.n_data


    def n_check_data(self):
        n_ninode = self.n_data.roots[0]
        
        #bsx flag
        # nose.tools.assert_equal(n_ninode.num_extra_data_list, 2) # TODO [object] UPB
        n_bsxflag = n_ninode.extra_data_list[0]
        n_gen_collision.n_check_bsx_flag(n_bsxflag)
        
        #check common collision
        n_bhkcollisionobject = n_gen_collision.n_check_bhkcollisionobject_data(n_ninode)
        n_bhkrigidbody =  n_gen_collision.n_check_bhkrigidbody_data(n_bhkcollisionobject)
        
        #check bhkboxshape specific data
        n_gen_bhkboxshape.n_check_bhkrigidbody_data(n_bhkrigidbody)
        n_bhktransform = n_gen_bhkboxshape.n_check_bhkconvextransform_data(n_bhkrigidbody)
        n_gen_bhkboxshape.n_check_bhkboxshape_data(n_bhktransform)
        
        #geometry
        n_trishape = n_ninode.children[0]
        n_gen_geometry.n_check_trishape(n_trishape)
        
        