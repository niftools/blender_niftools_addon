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
from bpy.types import Panel
   


class NifMatFlagPanel(Panel):
    bl_label = "Flag Panel"
    
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
        matalpha = context.material.niftools_alpha
        
        layout = self.layout
        row = layout.column()
        
        row.prop(matalpha, "alphaflag")
        row.prop(matalpha, "materialflag")
        row.prop(matalpha, "textureflag")
        

class NifMatColorPanel(Panel):
    bl_label = "Material Color Panel"
    
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
        row = layout.column()
        col_ambient_L = row.column()
        col_ambient_R = row.column()
        col_ambient_L.prop(mat, "ambient_preview")
        col_ambient_R.prop(mat, "ambient_color", text="")
        
        col_emissive_L = row.column()
        col_emissive_R = row.column()
        col_emissive_L.prop(mat, "emissive_preview")
        col_emissive_R.prop(mat, "emissive_color", text="")      


class NiftoolsBonePanel(Panel):
    bl_label = "Niftools Bone Props"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"

    @classmethod
    def poll(cls, context):
        return True
        

    def draw(self, context):
        nif_bone_props = context.bone.niftools_bone
        
        layout = self.layout
        row = layout.column()
        
        row.prop(nif_bone_props, "boneflags")
    


class NifShaderObjectPanel(Panel):
    bl_label = "Niftools Shader"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_options =  {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return True
        

    def draw(self, context):
        nif_obj_props = context.object.niftools_shader
        
        layout = self.layout
        row = layout.column()
        
        row.prop(nif_obj_props, "shadertype")
        
        if nif_obj_props.shadertype == 'BSShaderPPLightingProperty':
            row.prop(nif_obj_props, "bsspplp_shaderobjtype")
                    
            row.prop(nif_obj_props, "sf_specular")
            row.prop(nif_obj_props, "sf_skinned")
            row.prop(nif_obj_props, "sf_low_detail")
            row.prop(nif_obj_props, "sf_vertex_alpha")
            row.prop(nif_obj_props, "sf_unknown_1")
            row.prop(nif_obj_props, "sf_single_pass")
            row.prop(nif_obj_props, "sf_empty")
            row.prop(nif_obj_props, "sf_environment_mapping")
            row.prop(nif_obj_props, "sf_alpha_texture")
            row.prop(nif_obj_props, "sf_unknown_2")
            row.prop(nif_obj_props, "sf_face_gen")
            row.prop(nif_obj_props, "sf_parallax_shader_index_15")
            row.prop(nif_obj_props, "sf_unknown_3")
            row.prop(nif_obj_props, "sf_non_projective_shadows")
            row.prop(nif_obj_props, "sf_unknown_4")
            row.prop(nif_obj_props, "sf_refraction")
            row.prop(nif_obj_props, "sf_fire_refraction")
            row.prop(nif_obj_props, "sf_eye_environment_mapping")
            row.prop(nif_obj_props, "sf_hair")
            row.prop(nif_obj_props, "sf_dynamic_alpha")
            row.prop(nif_obj_props, "sf_localmap_hide_secret")
            row.prop(nif_obj_props, "sf_window_environment_mapping")
            row.prop(nif_obj_props, "sf_tree_billboard")
            row.prop(nif_obj_props, "sf_shadow_frustum")
            row.prop(nif_obj_props, "sf_multiple_textures")
            row.prop(nif_obj_props, "sf_remappable_textures")
            row.prop(nif_obj_props, "sf_decal_single_pass")
            row.prop(nif_obj_props, "sf_dynamic_decal_single_pass")
            row.prop(nif_obj_props, "sf_parallax_occulsion")
            row.prop(nif_obj_props, "sf_external_emittance")
            row.prop(nif_obj_props, "sf_shadow_map")
            row.prop(nif_obj_props, "sf_z_buffer_test")

        elif nif_obj_props.shadertype == 'BSLightingShaderProperty':
            row.prop(nif_obj_props, "bslsp_shaderobjtype")



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
        row = layout.column()
        row.prop(nif_obj_props, "rootnode")
        row.prop(nif_obj_props, "upb")
        row.prop(nif_obj_props, "bsxflags")
        row.prop(nif_obj_props, "consistency_flags")
        row.prop(nif_obj_props, "objectflags")
        row.prop(nif_obj_props, "longname")
        

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
        box.prop(col_setting, "deactivator_type", text='Deactivator Type') # motion dactivation prop
        box.prop(col_setting, "solver_deactivation", text='Solver Deactivator') # motion dactivation prop
        box.prop(col_setting, "quality_type", text='Quality Type') # quality type prop
        box.prop(col_setting, "oblivion_layer", text='Oblivion Layer') # oblivion layer prop
        box.prop(col_setting, "max_linear_velocity", text='max_linear_velocity') # oblivion layer prop
        box.prop(col_setting, "max_angular_velocity", text='max_angular_velocity') # oblivion layer prop
        box.prop(col_setting, "motion_system", text='Motion System') # motion system prop
        box.prop(col_setting, "havok_material", text='Havok Material') # havok material prop
        
        con_setting = context.active_object.niftools_constraint
                
        box.prop(con_setting, "LHMaxFriction", text='LHMaxFriction')
        box.prop(con_setting, "tau", text='tau')
        box.prop(con_setting, "damping", text='damping')

def register():
    bpy.utils.register_class(NifMatColorPanel)
    bpy.types.MATERIAL_PT_shading.prepend(NifMatColorPanel)
    bpy.utils.register_class(NifCollisionBoundsPanel)

def unregister():
    bpy.types.MATERIAL_PT_shading.remove(NifMatColorPanel)
    bpy.utils.unregister_class(NifMatColorPanel)
    bpy.utils.unregister_class(NifCollisionBoundsPanel)
    
