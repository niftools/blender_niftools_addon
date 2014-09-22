''' Nif User Interface, connect custom properties from properties.py into Blenders UI'''

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
from bpy.types import Panel, UIList


class ObjectPanel(Panel):
    bl_label = "Niftools Object Panel"
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        return True
        

    def draw(self, context):
        nif_obj_props = context.object.niftools
        ob = context.object
        
        layout = self.layout
        row = layout.column()
        row.prop(nif_obj_props, "nif_version")
        row.prop(nif_obj_props, "user_version")
        row.prop(nif_obj_props, "user_version_2")
        row.prop(nif_obj_props, "rootnode")
        row.prop(nif_obj_props, "bsnumuvset")
        row.prop(nif_obj_props, "upb")
        row.prop(nif_obj_props, "bsxflags")
        row.prop(nif_obj_props, "consistency_flags")
        row.prop(nif_obj_props, "objectflags")
        row.prop(nif_obj_props, "longname")

        row.prop(nif_obj_props, "extra_data_index")
#         if not context.object.nif_obj_props:
#             row.operator("object.niftools_bs_invmarker_add", icon='ZOOMIN', text="")
        row.operator("object.niftools_extradata_add", icon='ZOOMIN', text="")
        if len(context.object.niftools_bs_invmarker) == 0:
            row.operator("object.niftools_extradata_remove", icon='ZOOMOUT', text="")
        row.template_list("OBJECT_UL_ExtraData", "", nif_obj_props, "extra_data", nif_obj_props, "extra_data_index")

class OBJECT_UL_ExtraData(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(0.2)
        split.label(str(item.name))
        split.prop(item, "name", text="", emboss=False, translate=False, icon='BORDER_RECT')

class ObjectInvMarkerPanel(Panel):
    bl_label = "BS Inv Marker"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        return True
        

    def draw(self, context):       
        layout = self.layout
        nif_bsinv_props = context.object.niftools_bs_invmarker
                
        row = layout.row()
        if not context.object.niftools_bs_invmarker:
            row.operator("object.niftools_bs_invmarker_add", icon='ZOOMIN', text="")
        if context.object.niftools_bs_invmarker:
            row.operator("object.niftools_bs_invmarker_remove", icon='ZOOMOUT', text="")

        col = row.column(align=True)
        for i, x in enumerate(nif_bsinv_props):
            col.prop(nif_bsinv_props[i], "bs_inv_x", index= i)
            col.prop(nif_bsinv_props[i], "bs_inv_y", index= i)
            col.prop(nif_bsinv_props[i], "bs_inv_z", index= i)
            col.prop(nif_bsinv_props[i], "bs_inv_zoom", index= i)


def register():
    bpy.utils.register_class(ObjectPanel)
    bpy.utils.register_class(ObjectInvMarkerPanel)
    bpy.utils.register_class(OBJECT_UL_ExtraData)
    

def unregister():
    bpy.utils.unregister_class(ObjectPanel)
    bpy.utils.unregister_class(ObjectInvMarkerPanel)
    bpy.utils.unregister_class(OBJECT_UL_ExtraData)


