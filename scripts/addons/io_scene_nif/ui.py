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
def unregister():
    mat_emissive_prop = (lambda self, context: self.layout.prop(context.material.niftools, "emissive_color"))
    bpy.types.MATERIAL_PT_shading.remove(mat_emissive_prop)
