""" Nif User Interface, connect custom properties from properties.py into Blenders UI"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2015, NIF File Format Library and Tools contributors.
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

from bpy.types import Operator

from io_scene_niftools import properties
from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class BSXExtraDataAdd(Operator):
    """Adds BSX Flag to extra data of the currently selected object"""
    bl_idname = "object.niftools_extradata_bsx_add"
    bl_label = "Add BSX Flags"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        b_obj = context.active_object
        extradata = properties.object.BSXFlags
        b_obj.niftools.extra_data_store.extra_data.add()
        return {'FINISHED'}


class UPBExtraDataAdd(Operator):
    """Adds BSX Flags to extra data"""
    bl_idname = "object.niftools_extradata_upb_add"
    bl_label = "Add UPB"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        b_obj = context.active_object
        b_obj.niftools.extra_data_store.extra_data.add()
        return {'FINISHED'}


class SampleExtraDataAdd(Operator):
    """Sample"""
    bl_idname = "object.niftools_extradata_sample_add"
    bl_label = "Sample 1"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        b_obj = context.active_object
        b_obj.niftools.extra_data_store.extra_data.add()
        return {'FINISHED'}


class NiExtraDataRemove(Operator):
    """Removes Extra Data from Objects"""
    bl_idname = "object.niftools_extradata_remove"
    bl_label = "Remove Inventory Marker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        b_obj = context.active_object
        item = b_obj.niftools.extra_data_store.extra_data_index
        b_obj.niftools.extra_data_store.extra_data.remove(item)
        return {'FINISHED'}


classes = [
    BSXExtraDataAdd,
    UPBExtraDataAdd,
    SampleExtraDataAdd,
    NiExtraDataRemove
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
