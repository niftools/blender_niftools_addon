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
        
        
def register():
    mat_emissive_prop = (lambda self, context: self.layout.prop(context.material.niftools, "emissive_color"))
    bpy.types.MATERIAL_PT_shading.prepend(mat_emissive_prop)

    bpy.utils.register_class(NifCollisionBoundsPanel)


def unregister():
    mat_emissive_prop = (lambda self, context: self.layout.prop(context.material.niftools, "emissive_color"))
    bpy.types.MATERIAL_PT_shading.remove(mat_emissive_prop)
    
    bpy.utils.unregister_class(NifCollisionBoundsPanel)
    
