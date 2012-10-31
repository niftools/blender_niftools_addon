''' Nif User Interface, connect custom properties from properties.py into Blenders UI'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2012, NIF File Format Library and Tools contributors.
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
from bpy.types import Panel
   
class NifEmissivePanel(Panel):
    bl_label = "Emission Panel"
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    
    @classmethod
    def poll(cls, context):
        mat = context.material
        if mat is not None:
            if mat.use_nodes:
                if mat.active_node_material is not None:
                    return True
                return False
            return True
        return False
    
    def draw(self, context):
        mat = context.material.niftools
        
        layout = self.layout
        row = layout.row()
        colL = row.column()
        colR = row.column()
        colL.prop(mat, "emissive_preview")
        colR.prop(mat, "emissive_color", text="")      

class NifObjectPanel(Panel):
    bl_label = "Niftools Object Panel"
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        return True
        
    def draw(self, context):
        nif_obj_props = context.object.niftools
        
        layout = self.layout
        row = layout.row()
        row.prop(nif_obj_props, "upb")

class NifCollisionBoundsPanel(Panel):
    bl_label = "Collision Bounds"
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"
    '''
    @classmethod
    def poll(cls, context):
    '''

    def draw_header(self, context):
        game = context.active_object.game
        self.layout.prop(game, "use_collision_bounds", text="")

    def draw(self, context):
        layout = self.layout

        game = context.active_object.game
        col_setting = context.active_object.nifcollision
        
        layout.active = game.use_collision_bounds
        layout.prop(game, "collision_bounds_type", text="Bounds")
        
        box = layout.box()
        box.active = game.use_collision_bounds
        
        box.prop(col_setting, "col_filter", text='Col Filter') # col filter prop       
        box.prop(col_setting, "quality_type", text='Quality Type') # quality type prop
        box.prop(col_setting, "oblivion_layer", text='Oblivion Layer') # oblivion layer prop 
        box.prop(col_setting, "motion_system", text='Motion System') # motion system prop
        box.prop(col_setting, "havok_material", text='Havok Material') # havok material prop

def register():
    bpy.utils.register_class(NifEmissivePanel)
    bpy.types.MATERIAL_PT_shading.prepend(NifEmissivePanel)
    bpy.utils.register_class(NifCollisionBoundsPanel)

def unregister():
    bpy.types.MATERIAL_PT_shading.remove(NifEmissivePanel)
    bpy.utils.unregister_class(NifEmissivePanel)
    bpy.utils.unregister_class(NifCollisionBoundsPanel)
    
