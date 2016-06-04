import bpy

from bpy.types import PropertyGroup
from bpy.props import (PointerProperty,
                       StringProperty,
                       IntProperty,
                       EnumProperty,
                       CollectionProperty,
                       FloatProperty
                       )

from pyffi.formats.nif import NifFormat

from io_scene_nif.properties.object.extra_data import ExtraDataStore

class ObjectProperty(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.niftools = PointerProperty(
                        name='Niftools Object Property',
                        description='Additional object properties used by the Nif File Format',
                        type=cls,
                        )

        cls.rootnode = EnumProperty(
                        name='Nif Root Node',
                        description='Type of property used to display meshes.',
                        items=(('NiNode', 'NiNode', "", 0),
                                ('BSFadeNode', 'BSFadeNode', "", 1)),
                        default='NiNode',
                        )
        
        cls.bsnumuvset = IntProperty(
                        name='BS Num UV Set',
                        default=0
                        )
        
        cls.longname = StringProperty(
                        name='Nif Long Name'
                        )

        cls.consistency_flags = EnumProperty(
                        name='Consistency Flag',
                        description='Controls animation type',
                        items=[(item, item, "", i) for i, item in enumerate(NifFormat.ConsistencyType._enumkeys)],
                        # default = 'SHADER_DEFAULT'
                        )

        cls.objectflags = IntProperty(
                        name='Object Flag',
                        description='Controls animation and collision',
                        default=0
                        )

        cls.bsxflags = IntProperty(
                        name='BSX Flags',
                        description='Controls animation and collision',
                        default=0  # 2 = Bit 1, enable collision
                        )

        cls.upb = StringProperty(
                        name='UPB',
                        description='Commands for an optimizer?',
                        default=''
                        )

        cls.extra_data_store = PointerProperty(
                        name="Extra Data",
                        description="Used to store all the Extra data",
                        type=ExtraDataStore,
                        )
        
        
    @classmethod
    def unregister(cls):
        del bpy.types.Object.niftools   
