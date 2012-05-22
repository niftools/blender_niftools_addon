''' Nif User Interface '''
''' Integrates the custom properties from properties.py into Blenders UI'''

import bpy

from bpy.types import Panel

class PhysicsButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"

class NifCollisionBoundsPanel(PhysicsButtonsPanel, Panel):
    bl_label = "Collision Bounds"
    
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
        
        #col filter prop
        box.prop(col_setting, "col_filter", text='Col Filter')

        #quality type prop
        box.prop(col_setting, "quality_type", text='Quality Type')
        
        #oblivion layer prop
        box.prop(col_setting, "oblivion_layer", text='Oblivion Layer')
    
        #motion system prop
        box.prop(col_setting, "motion_system", text='Motion System')
    
        #havok material prop
        box.prop(col_setting, "havok_material", text='Havok Material')
        
        
class NifEmissivePanel(Panel):
    bl_label = "Emission Panel"
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    
    
    def draw(self, context):
        mat = context.material.niftools
        
        layout = self.layout
        row = layout.row()
        colL = row.column()
        colR = row.column()
        colL.prop(mat, "emissive_preview")
        colR.prop(mat, "emissive_color", text="")
        
def register():
    
    bpy.utils.register_class(NifEmissivePanel)
    bpy.types.MATERIAL_PT_shading.prepend(NifEmissivePanel)
    bpy.utils.register_class(NifCollisionBoundsPanel)


def unregister():
    
    bpy.types.MATERIAL_PT_shading.remove(NifEmissivePanel)
    bpy.utils.unregister_class(NifEmissivePanel)
    bpy.utils.unregister_class(NifCollisionBoundsPanel)
    
