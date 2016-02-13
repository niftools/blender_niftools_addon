import bpy

from bpy.types import PropertyGroup
from bpy.props import (PointerProperty,
                       StringProperty,
                       IntProperty)

class Scene(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.niftools = PointerProperty(
                        name='Niftools Scene Property',
                        description='Additional scene properties used by the Nif File Format',
                        type=cls
                        )

        cls.nif_version = IntProperty(
                        name='Nif Version',
                        default=0
                        )

        cls.user_version = IntProperty(
                        name='User Version',
                        default=0
                        )

        cls.user_version_2 = IntProperty(
                        name='User Version 2',
                        default=0
                        )

    @classmethod
    def unregister(cls):
        del bpy.types.Scene.niftools