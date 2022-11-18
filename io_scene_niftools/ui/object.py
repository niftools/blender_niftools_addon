""" Nif User Interface, connect custom properties from properties.py into Blenders UI"""

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

from bpy.types import Panel, UIList, Menu

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class ObjectButtonsPanel(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @staticmethod
    def is_root_object(b_obj):
        return b_obj.parent is None

class ObjectPanel(ObjectButtonsPanel):
    bl_label = "Niftools Object Property"
    bl_idname = "NIFTOOLS_PT_ObjectPanel"

    # noinspection PyUnusedLocal
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        b_obj = context.object
        nif_obj_props = b_obj.niftools

        layout = self.layout
        row = layout.column()
        if self.is_root_object(b_obj):
            if b_obj.type == "EMPTY":
                row.prop(nif_obj_props, "nodetype")
            row.prop(nif_obj_props, "prn_location")
            row.prop(nif_obj_props, "upb")
            row.prop(nif_obj_props, "bsxflags")
        if b_obj.type == "MESH":
            # consistency flags only exist for NiGeometry
            row.prop(nif_obj_props, "consistency_flags")
        row.prop(nif_obj_props, "flags")
        row.prop(nif_obj_props, "longname")

        parent = b_obj.parent
        if parent and parent.type == 'ARMATURE':
            row.prop_search(nif_obj_props, "skeleton_root", parent.data, "bones")


class ObjectExtraData(ObjectButtonsPanel):
    bl_label = "Niftools Object Extra Data"
    bl_idname = "NIFTOOLS_PT_ObjectExtraDataPanel"

    # noinspection PyUnusedLocal
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        b_obj = context.object
        extra_data_store = b_obj.niftools.extra_data_store
        has_extra_data = len(extra_data_store.extra_data) > 0

        layout = self.layout

        row = layout.row()
        row.template_list("NIFTOOLS_UL_ExtraData", "", extra_data_store, "extra_data", extra_data_store,
                          "extra_data_index")

        # Add/Remove operators
        col = row.column(align=True)
        col.menu("NIFTOOLS_MT_ExtraDataType", icon='ZOOM_IN', text="")

        if has_extra_data:
            col.operator("object.niftools_extradata_remove", icon='ZOOM_OUT', text="")

        if has_extra_data:
            layout.row()
            box = layout.box()

            selected_extra_data = extra_data_store.extra_data[extra_data_store.extra_data_index]
            box.prop(selected_extra_data, "name")
            box.prop(selected_extra_data, "data")
            box.prop(selected_extra_data, "sub_class")


class ObjectExtraDataType(Menu):
    bl_label = "Niftools Extra Data Types"
    bl_idname = "NIFTOOLS_MT_ExtraDataType"

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        layout.operator("object.niftools_extradata_bsx_add")
        layout.operator("object.niftools_extradata_upb_add")
        layout.operator("object.niftools_extradata_sample_add")
        layout.operator("object.niftools_extradata_sample_add")


class ObjectExtraDataList(UIList):
    bl_label = "Niftools Extra Data List"
    bl_idname = "NIFTOOLS_UL_ExtraData"

    # noinspection PyUnusedLocal
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.2)
        split.label(text=str(item.name))
        split.prop(item, "data", text="", emboss=False, translate=False, icon='BORDERMOVE')


class ObjectBSInvMarkerPanel(ObjectButtonsPanel):
    bl_label = "Niftools BS Inv Marker"
    bl_idname = "NIFTOOLS_PT_ObjectBSInvMarker"
    bl_parent_id = "NIFTOOLS_PT_ObjectPanel"

    # noinspection PyUnusedLocal
    @classmethod
    def poll(cls, context):
        return cls.is_root_object(context.object)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        bs_inv = context.object.niftools.bs_inv
        if not bs_inv:
            row.operator("object.bs_inv_marker_add", icon='ZOOM_IN', text="")
        else:
            row.operator("object.bs_inv_marker_remove", icon='ZOOM_OUT', text="")
        col = row.column(align=True)
        for i, x in enumerate(bs_inv):
            col.prop(bs_inv[i], "x", index=i)
            col.prop(bs_inv[i], "y", index=i)
            col.prop(bs_inv[i], "z", index=i)
            col.prop(bs_inv[i], "zoom", index=i)


classes = [
    ObjectExtraDataList,
    ObjectExtraDataType,
    ObjectExtraData,
    ObjectPanel,
    ObjectBSInvMarkerPanel,
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
