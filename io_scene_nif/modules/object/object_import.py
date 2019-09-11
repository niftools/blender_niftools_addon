"""This script contains helper methods to export objects."""

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
import mathutils

from pyffi.formats.nif import NifFormat


class Object:
    # this will have to deal with all naming issues
    def __init__(self, parent):
        self.nif_import = parent
        # self.dict_names = {}
        # self.dict_blocks = {}
    
    def import_bsbound_data(self, root_block):
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.BSBound):
                self.nif_import.boundhelper.import_bounding_box(n_extra)
                    
    @staticmethod    
    def import_bsxflag_data(root_block):
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.BSXFlags):
                # get bsx flags so we can attach it to collision object
                bsxflags = n_extra.integer_data
                return bsxflags
        return 0

    @staticmethod
    def import_upbflag_data(root_block):
        # process extra data
        for n_extra in root_block.get_extra_datas():
            if isinstance(n_extra, NifFormat.NiStringExtraData):
                if n_extra.name.decode() == "UPB":
                    upbflags = n_extra.string_data.decode()
                    return upbflags
        return ''

    
    def create_b_obj(self, n_block, b_obj_data):
        """Helper function to create a b_obj from b_obj_data, link it to the current scene, make it active and select it."""
        # get the actual nif name
        n_name = n_block.name.decode()
        # let blender choose a name
        b_obj = bpy.data.objects.new(n_name, b_obj_data)
        b_obj.select = True
        # make the object visible and active
        bpy.context.scene.objects.link(b_obj)
        bpy.context.scene.objects.active = b_obj
        self.store_longname(b_obj, n_name)
        self.map_names(b_obj, n_block)
        return b_obj
        
    def store_longname(self, b_obj, n_name):
        """Save original name as object property, for export"""
        if b_obj.name != n_name:
            b_obj.niftools.longname = n_name
            # NifLog.debug("Stored long name for {0}".format(b_obj.name))
   
    def map_names(self, b_obj, n_block):
        """Create mapping between nif and blender names"""
        # map nif block to blender short name
        self.nif_import.dict_names[n_block] = b_obj.name
        # map blender short name to nif block
        self.nif_import.dict_blocks[b_obj.name] = n_block
        
        