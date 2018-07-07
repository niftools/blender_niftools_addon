import bpy
from bpy.props import PointerProperty, IntProperty
from bpy.types import PropertyGroup


class Scene(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.niftools_scene = PointerProperty(
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
        del bpy.types.Scene.niftools_scene
