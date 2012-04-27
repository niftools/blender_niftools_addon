import bpy

#TODO_3.0 - Improve placement of props, possibly add a preview button
'''
from bpy.types import Panel

class NiftoolsMaterialPanel(Panel):
    bl_label = "Niftools Material Panel"
    bl_idname = "OBJECT_PT_niftools_utilities"
    
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    
    def draw(self, context):
        layout = self.layout
        material = context.material.niftools
        
        #material color swatches
        row = layout.row()
        row.prop(material, "diffuse_color")
        row = layout.row()
        row.prop(material, "ambient_color")
        
        row = layout.row()
        row.prop(material, "emissive_color")

def material(
layout = (lambda self, context: self.layout)
row = (lambda self, context: layout.row())
split = (lambda self, context: row.split(percentage=0.5))
colL = (lambda self, context: split.column())
colL_prop = (lambda self, context: colL.prop(context.material.niftools, "emissive_color"))
colR = split.column()
'''


def register():
    mat_emissive_prop = (lambda self, context: self.layout.prop(context.material.niftools, "emissive_color"))
    bpy.types.MATERIAL_PT_shading.prepend(mat_emissive_prop)

    #col filter prop
    coll_cf_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "col_filter"))
    bpy.types.PHYSICS_PT_game_physics.prepend(coll_cf_prop)

    #quality type prop
    coll_qt_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "quality_type"))
    bpy.types.PHYSICS_PT_game_physics.prepend(coll_qt_prop)

    #oblivion layer prop
    coll_obl_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "oblivion_layer"))
    bpy.types.PHYSICS_PT_game_physics.prepend(coll_obl_prop)

    #motion system prop
    coll_mosys_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "motion_system"))
    bpy.types.PHYSICS_PT_game_physics.prepend(coll_mosys_prop)

   #havok material prop
    coll_hm_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "havok_material"))
    bpy.types.PHYSICS_PT_game_physics.prepend(coll_hm_prop)

   #use blende props prop
    coll_bp_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "use_blender_properties"))
    bpy.types.PHYSICS_PT_game_physics.prepend(coll_bp_prop)


def unregister():
    mat_emissive_prop = (lambda self, context: self.layout.prop(context.material.niftools, "emissive_color"))
    bpy.types.MATERIAL_PT_shading.remove(mat_emissive_prop)

    #col filter prop
    coll_cf_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "col_filter"))
    bpy.types.PHYSICS_PT_game_physics.remove(coll_cf_prop)

    #quality type prop
    coll_qt_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "quality_type"))
    bpy.types.PHYSICS_PT_game_physics.remove(coll_qt_prop)

    #oblivion layer prop
    coll_obl_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "oblivion_layer"))
    bpy.types.PHYSICS_PT_game_physics.remove(coll_obl_prop)

    #motion system prop
    coll_mosys_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "motion_system"))
    bpy.types.PHYSICS_PT_game_physics.remove(coll_mosys_prop)

    #havok material prop
    coll_hm_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "havok_material"))
    bpy.types.PHYSICS_PT_game_physics.remove(coll_hm_prop)

    #use blender props prop
    coll_bp_prop = (lambda self, context: self.layout.prop(context.object.nifcollision, "use_blender_properties"))
    bpy.types.PHYSICS_PT_game_physics.remove(coll_bp_prop)
