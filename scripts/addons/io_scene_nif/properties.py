import bpy
from bpy.props import (PointerProperty, 
                       FloatVectorProperty)

class NiftoolsMaterialProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Material.niftools = PointerProperty(
                        name="Niftools Materials",
                        description = "Additional setting for use with the nif format",
                        type=cls,
                        )
        
        cls.diffuse_color = FloatVectorProperty(
                name='Diffuse', subtype='COLOR', default=[1.0,1.0,1.0],min=0.0, max=1.0)
        
        cls.ambient_color = FloatVectorProperty(
                name='Ambient', subtype='COLOR', default=[1.0,1.0,1.0],min=0.0, max=1.0)
        
        cls.emissive_color = FloatVectorProperty(
                name='Emissive', subtype='COLOR', default=[0.0,0.0,0.0],min=0.0, max=1.0)
    
    @classmethod
    def unregister(cls):
        del bpy.types.Material.niftools

def register():
    bpy.utils.register_class(NiftoolsMaterialProps)

def unregister():
    bpy.utils.unregister_class(NiftoolsMaterialProps)