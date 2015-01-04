"""Exports and imports mesh data"""

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

from integration import SingleNif
from integration.data import gen_data 
from integration.geometry.vertex import b_gen_vertex
from integration.geometry.vertex import n_gen_vertex

class TestVertex(SingleNif):
    """Test base geometry, single blender object."""

    n_name = 'geometry/vertex/test_vertex' # (documented in base class)
    b_name = 'Cube'

    def b_create_header(self):
        self.n_game = 'OBLIVION'

    def b_create_data(self):
        # (documented in base class)
        b_obj = b_gen_vertex.b_create_cube(self.b_name)
        
        # transform it into something less trivial
        b_gen_vertex.b_transform_cube(b_obj)
    
    def b_check_data(self):
        b_obj = bpy.data.objects[self.b_name]
        b_gen_vertex.b_check_geom_obj(b_obj)

    def n_create_header(self):
        gen_data.n_create_header_oblivion(self.n_data)

    def n_create_data(self):
        n_gen_vertex.n_create_blocks(self.n_data)
        return self.n_data

    def n_check_data(self):
        n_trishape = self.n_data.roots[0].children[0]
        n_gen_vertex.n_check_trishape(n_trishape)

