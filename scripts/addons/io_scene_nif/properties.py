'''Nif Properties'''
'''Make custom nif properties accessible via Blender object types''' 

import bpy
from bpy.props import (PointerProperty, 
                       FloatVectorProperty,
                       StringProperty,
                       IntProperty,
                       BoolProperty,
                       EnumProperty
                       )

import site
from pyffi.formats.nif import NifFormat

def underscore_to_camelcase(s):
    """Take the underscore-separated string s and return a camelCase
    equivalent.  Initial and final underscores are preserved, and medial
    pairs of underscores are turned into a single underscore."""
    def camelcase_words(words):
        first_word_passed = False
        for word in words:
            
            if not word:
                yield "_"
                continue
            if first_word_passed:
                yield word.capitalize()
            else:
                yield word.lower()
            first_word_passed = True
    return ''.join(camelcase_words(s.split('_')))

class NiftoolsMaterialProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Material.niftools = PointerProperty(
                        name='Niftools Materials',
                        description = 'Additional material properties used by the Nif File Format',
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
                        name='Niftools Object Property',
                        description = 'Additional object properties used by the Nif File Format',
                        type = cls,
                        )
        cls.longname = StringProperty(
                        name = 'Nif LongName'
                        )

    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools   


class NiftoolsObjectCollisionProps(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):

        #physics
        bpy.types.Object.nifcollision = PointerProperty(
                        name='Niftools Collision Property',
                        description = 'Additional collision properties used by the Nif File Format',
                        type = cls,
                        )
        
        cls.motion_system = EnumProperty(
                        name='Motion System',
                        description = 'Havok Motion System settings for bhkRigidBody(t)',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.MotionSystem._enumkeys)],
                        #default = 'MO_SYS_FIXED',
                        
                        )
           
        cls.oblivion_layer = EnumProperty(
                        name = 'Oblivion Layer',
                        description = 'Mesh color, used in Editor',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.OblivionLayer._enumkeys)],
                        #default = 'OL_STATIC',
                        )
          
        cls.quality_type = EnumProperty(
                        name = 'Quality Type',
                        description = 'Determines quality of motion',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.MotionQuality._enumkeys)],
                        #default = 'MO_QUAL_FIXED',
                        )
        
        cls.col_filter = IntProperty(
                        name = 'Col Filter',
                        description = 'Flags for bhkRigidBody(t)',
                        default = 0
                        )
        
        cls.havok_material = EnumProperty(
                        name = 'Havok Material',
                        description = 'The Shapes material',
                        items = [(item, item,"", i) for i, item in enumerate(NifFormat.HavokMaterial._enumkeys)],
                        #default = 'HAV_MAT_WOOD'
                        )
        
        cls.bsxFlags = IntProperty(
                        name = 'BSXFlags',
                        description = 'Controls animation and collision',
                        default = 2 #2 = Bit 1, enable collision
                        )
        
        cls.upb = StringProperty(
                        name = 'UPB',
                        description = 'Commands for an optimizer?',
                        default = 'Mass = 0.000000 Ellasticity = 0.300000 Friction = 0.300000 Simulation_Geometry = 2 Proxy_Geometry = <None> Use_Display_Proxy = 0 Display_Children = 1 Disable_Collisions = 0 Inactive = 0 Display_Proxy = <None> Collision_Groups = 1 Unyielding = 1 '
                        )
                        
        cls.export_bhklist = BoolProperty(
                                name = 'Export BHKList',
                                description = 'None',
                                default = False
                                )
        
        cls.use_blender_properties = BoolProperty(
                        name = 'Use Blender Properties',
                        description = 'Whether or not to export collision settings via blender properties',
                        default = False,
                        )
    @classmethod
    def unregister(cls):
        del bpy.types.Object.nifcollision
        
def register():
    
    bpy.utils.register_class(NiftoolsMaterialProps)
    bpy.utils.register_class(NiftoolsObjectProps)
    bpy.utils.register_class(NiftoolsObjectCollisionProps)

def unregister():
    bpy.utils.unregister_class(NiftoolsMaterialProps)
    bpy.utils.unregister_class(NiftoolsObjectProps)
    bpy.utils.unregister_class(NiftoolsObjectCollisionProps)
