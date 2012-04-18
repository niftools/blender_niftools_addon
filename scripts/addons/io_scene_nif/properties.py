import bpy
from bpy.props import (PointerProperty, 
                       FloatVectorProperty,
                       StringProperty,
                       IntProperty,
                       BoolProperty
                       )

class NiftoolsMaterialProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Material.niftools = PointerProperty(
                        name="Niftools Materials",
                        description = "Additional material properties used by the Nif File Format",
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

class NiftoolsObjectProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools = PointerProperty(
                        name="Niftools Object Property",
                        description = "Additional object properties used by the Nif File Format",
                        type = cls,
                        )
        cls.longname = StringProperty(
                name = 'Nif LongName')

class NiftoolsCollisionProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.nifcollision = PointerProperty(
                                                         name="Niftools Collision Property",
                                                         description = "Additional collision properties used by the Nif File Format",
                                                         type = cls,
                                                         )
        cls.motion_system = StringProperty(
                                           name="Motion System",
                                           description = "Havok Motion System settings for bhkRigidBody(t)",
                                           default = "MO_SYS_FIXED"
                                           )      
        cls.oblivion_layer = StringProperty(
                                            name = "Oblivion Layer",
                                            description = "Mesh color when in Oblivion CS",
                                            default = "OL_STATIC"
                                            )  
        cls.quality_type = StringProperty(
                                          name = "Quality Type",
                                          description = "Determines quality of motion",
                                          default = "MO_QUAL_FIXED"
                                          )
        cls.col_filter = IntProperty(
                                     name = "Col Filter",
                                     description = "Flags for bhkRigidBody(t)",
                                     default = 0
                                    )
        cls.havok_material = StringProperty(
                                            name = "Havok Material",
                                            description = "The Shapes material",
                                            default = "HAV_MAT_WOOD"
                                            )
        cls.use_blender_properties = BoolProperty(
                                                  name = "Use Blender Properties",
                                                  description = "Whether or not to export collision settings via blender properties",
                                                  default = True,
                                                  )
        cls.export_bhklist = BoolProperty(
                                          name = "Export BHKList",
                                          description = "None",
                                          default = False
                                          )
        cls.bsxFlags = IntProperty(
                                   name = "BSXFlags",
                                   description = "Controls animation and collision",
                                   default = 2 #2 = Bit 1, enable collision
                                   )
        
        

def register():
    bpy.utils.register_class(NiftoolsMaterialProps)
    bpy.utils.register_class(NiftoolsObjectProps)

def unregister():
    bpy.utils.unregister_class(NiftoolsMaterialProps)
    bpy.utils.unregister_class(NiftoolsObjectProps)