""" Nif User Interface, connect custom geometry properties from properties.py into Blenders UI"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2014, NIF File Format Library and Tools contributors.
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
from bpy.types import Operator

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class BsInvMarkerAdd(Operator):
    """Adds BsInvMarker set"""
    bl_idname = "object.niftools_bs_invmarker_add"
    bl_label = "Add Inventory Marker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        b_obj_invmarker = obj.niftools_bs_invmarker.add()
        b_obj_invmarker.name = "INV"
        b_obj_invmarker.bs_inv_x = 0
        b_obj_invmarker.bs_inv_y = 0
        b_obj_invmarker.bs_inv_z = 0
        b_obj_invmarker.bs_inv_zoom = 1
        return {'FINISHED'}


class BsInvMarkerRemove(bpy.types.Operator):
    """Removes BsInvMarker set"""
    bl_idname = "object.niftools_bs_invmarker_remove"
    bl_label = "Remove Inventory Marker"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        item = len(context.active_object.niftools_bs_invmarker) - 1
        obj = context.active_object
        obj.niftools_bs_invmarker.remove(item)
        return {'FINISHED'}


class NfTlPartFlagAdd(bpy.types.Operator):
    """Adds Dismember partition Flag set"""
    bl_idname = "object.niftools_part_flags_add"
    bl_label = "Add Dismember Flags"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        b_obj_invmarker = obj.niftools_part_flags.add()
        obj.niftools_part_flags_panel.pf_partcount = len(obj.niftools_part_flags)
        return {'FINISHED'}


class NfTlPartFlagRemove(bpy.types.Operator):
    """Removes Dismember partition Flag set"""
    bl_idname = "object.niftools_part_flags_remove"
    bl_label = "Remove Dismember Flags"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        item = len(context.active_object.niftools_part_flags) - 1
        obj = context.active_object
        obj.niftools_part_flags.remove(item)
        obj.niftools_part_flags_panel.pf_partcount = len(obj.niftools_part_flags)
        return {'FINISHED'}


classes = [
    BsInvMarkerAdd,
    BsInvMarkerRemove,
    NfTlPartFlagAdd,
    NfTlPartFlagRemove
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
