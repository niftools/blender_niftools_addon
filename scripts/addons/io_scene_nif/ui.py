import bpy

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
        '''
        row = layout.row()
        row.prop(material, "diffuse_color")
        row = layout.row()
        row.prop(material, "ambient_color")
        '''
        
        row = layout.row()
        row.prop(material, "emissive_color")
        

