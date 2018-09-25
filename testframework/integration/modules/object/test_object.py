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
from integration.data import n_gen_header, b_gen_header
from integration.modules.object import b_gen_object, n_gen_object

PATH = 'object/test_object'


class TestNiNode(SingleNif):
    """Test base geometry, single blender object."""

    g_path = PATH  # (documented in base class)
    g_name = 'test_object'
    b_name = 'NifObject'

    def b_create_header(self):
        b_gen_header.b_create_oblivion_info()
    
    def b_create_data(self):
        b_gen_object.b_create_transformed_object(self.b_name)
        
    def b_check_data(self):
        b_gen_header.b_check_oblivion_info()
        b_obj = bpy.data.objects[self.b_name]
        b_gen_object.b_check_transform(b_obj)

    def n_create_header(self):
        n_gen_header.n_create_header_oblivion(self.n_data)

    def n_create_data(self):
        n_gen_object.n_create_blocks(self.n_data)

    def n_check_data(self):
        n_ninode = self.n_data.roots[0].children[0]
        n_gen_object.n_check_ninode(n_ninode)
        n_gen_object.n_check_transform(n_ninode)
