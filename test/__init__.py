"""Package for regression testing of the blender nif scripts."""

import bpy

def setup(self):
    """Enables the nif scripts addon, so all tests can use it."""
    bpy.ops.wm.addon_enable(module="io_scene_nif")

def teardown(self):
    """Disables the nif scripts addon."""
    bpy.ops.wm.addon_disable(module="io_scene_nif")
