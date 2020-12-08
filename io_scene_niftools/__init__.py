"""Blender Niftools Addon for import and export."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2007, NIF File Format Library and Tools contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import logging
import os
import sys

import bpy
import bpy.props

# updater ops import, all setup in this file
from . import addon_updater_ops

# Python dependencies are bundled inside the io_scene_nif/dependencies folder
current_dir = os.path.dirname(__file__)
_dependencies_path = os.path.join(current_dir, "dependencies")
if _dependencies_path not in sys.path:
    sys.path.append(_dependencies_path)
del _dependencies_path

import io_scene_niftools
from io_scene_niftools import properties, operators, ui, update

from io_scene_niftools.utils.logging import NifLog
with open(os.path.join(current_dir, "VERSION.txt")) as version:
    NifLog.info(f"Loading: Blender Niftools Addon: {version.read()}")

import pyffi
NifLog.info(f"Loading: Pyffi: {pyffi.__version__}")

from io_scene_niftools.utils import debugging

# Blender addon info.
bl_info = {
    "name": "NetImmerse/Gamebryo format support",
    "description": "Import and export files in the NetImmerse/Gamebryo formats (.nif, .kf, .egm)",
    "author": "Niftools team",
    "blender": (2, 81, 0),
    "version": (0, 0, 3),  # can't read from VERSION, blender wants it hardcoded
    "api": 39257,
    "location": "File > Import-Export",
    "warning": "Partially functional port from 2.49 series still in progress",
    "wiki_url": "https://blender-niftools-addon.readthedocs.io/",
    "tracker_url": "https://github.com/niftools/blender_niftools_addon/issues",
    "support": "COMMUNITY",
    "category": "Import-Export"
}


def _init_loggers():
    """Set up loggers."""
    pyffi_logger = logging.getLogger("pyffi")
    pyffi_logger.setLevel(logging.WARNING)
    niftools_logger = logging.getLogger("niftools")
    niftools_logger.setLevel(logging.WARNING)
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
    log_handler.setFormatter(log_formatter)
    niftools_logger.addHandler(log_handler)
    pyffi_logger.addHandler(log_handler)


# noinspection PyUnusedLocal
def menu_func_import(self, context):
    self.layout.operator(operators.nif_import_op.NifImportOperator.bl_idname, text="NetImmerse/Gamebryo (.nif)")
    self.layout.operator(operators.kf_import_op.KfImportOperator.bl_idname, text="NetImmerse/Gamebryo (.kf)")
    self.layout.operator(operators.egm_import_op.EgmImportOperator.bl_idname, text="NetImmerse/Gamebryo (.egm)")
    # TODO [general] get default path from config registry
    # default_path = bpy.data.filename.replace(".blend", ".nif")
    # ).filepath = default_path


# noinspection PyUnusedLocal
def menu_func_export(self, context):
    self.layout.operator(operators.nif_export_op.NifExportOperator.bl_idname, text="NetImmerse/Gamebryo (.nif)")
    # self.layout.operator(operators.kf_export_op.KfExportOperator.bl_idname, text="NetImmerse/Gamebryo (.kf)")


# we have to 'register' the operators so we can access them like this to register them for blender
operators.register()
properties.register()
ui.register()
# todo [general] add more properties, make sure they show up
classes = (
    operators.egm_import_op.EgmImportOperator,
    operators.kf_import_op.KfImportOperator,
    operators.geometry.BsInvMarkerAdd,
    operators.geometry.BsInvMarkerRemove,
    operators.geometry.NfTlPartFlagAdd,
    operators.geometry.NfTlPartFlagRemove,
    operators.object.BSXExtraDataAdd,
    operators.object.UPBExtraDataAdd,
    operators.object.SampleExtraDataAdd,
    operators.object.NiExtraDataRemove,
    operators.nif_import_op.NifImportOperator,
    operators.nif_export_op.NifExportOperator,

    properties.armature.BoneProperty,
    properties.armature.ArmatureProperty,

    properties.collision.CollisionProperty,

    properties.constraint.ConstraintProperty,

    properties.geometry.SkinPartHeader,
    properties.geometry.SkinPartFlags,

    properties.material.Material,
    properties.material.AlphaFlags,

    properties.object.ExtraData,
    properties.object.ExtraDataStore,
    properties.object.ObjectProperty,
    properties.object.BsInventoryMarker,

    properties.scene.Scene,

    properties.shader.ShaderProps,

    ui.armature.BonePanel,
    ui.armature.ArmaturePanel,

    ui.collision.CollisionBoundsPanel,

    ui.geometry.PartFlagPanel,

    ui.material.MaterialFlagPanel,
    ui.material.MaterialColorPanel,

    ui.operator.OperatorImportIncludePanel,
    ui.operator.OperatorImportTransformPanel,
    ui.operator.OperatorImportArmaturePanel,
    ui.operator.OperatorImportAnimationPanel,
    ui.operator.OperatorExportTransformPanel,
    ui.operator.OperatorExportArmaturePanel,
    ui.operator.OperatorExportAnimationPanel,
    ui.operator.OperatorExportOptimisePanel,
    ui.operator.OperatorCommonDevPanel,

    ui.object.ObjectPanel,
    ui.object.ObjectExtraData,
    ui.object.ObjectExtraDataType,
    ui.object.ObjectExtraDataList,
    ui.object.ObjectBSInvMarkerPanel,

    ui.scene.ScenePanel,

    ui.scene.SceneVersionInfoPanel,

    ui.shader.ShaderPanel,

    update.UpdaterPreferences,
    )


def register():
    # addon updater code and configurations in case of broken version, try to register the updater first
    # so that users can revert back to a working version
    configure_autoupdater()

    _init_loggers()
    operators.register()
    properties.register()
    ui.register()
    from bpy.utils import register_class
    for cls in classes:
        # addon_updater_ops.make_annotations(cls)  # to avoid blender 2.8 warnings
        register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    # register all property groups after their classes have been registered
    bpy.types.Armature.niftools = bpy.props.PointerProperty(type=properties.armature.ArmatureProperty)
    bpy.types.Bone.niftools = bpy.props.PointerProperty(type=properties.armature.BoneProperty)
    bpy.types.Material.niftools = bpy.props.PointerProperty(type=properties.material.Material)
    bpy.types.Material.niftools_alpha = bpy.props.PointerProperty(type=properties.material.AlphaFlags)
    bpy.types.Material.niftools_shader = bpy.props.PointerProperty(type=properties.shader.ShaderProps)
    bpy.types.Object.nifcollision = bpy.props.PointerProperty(type=properties.collision.CollisionProperty)
    bpy.types.Object.niftools = bpy.props.PointerProperty(type=properties.object.ObjectProperty)
    bpy.types.Object.niftools_bs_invmarker = bpy.props.CollectionProperty(type=properties.object.BsInventoryMarker)
    bpy.types.Object.niftools_constraint = bpy.props.PointerProperty(type=properties.constraint.ConstraintProperty)
    bpy.types.Object.niftools_part_flags = bpy.props.CollectionProperty(type=properties.geometry.SkinPartFlags)
    bpy.types.Object.niftools_part_flags_panel = bpy.props.PointerProperty(type=properties.geometry.SkinPartHeader)
    bpy.types.Scene.niftools_scene = bpy.props.PointerProperty(type=properties.scene.Scene)


def select_zip_file(self, tag):
    """Select the latest build artifact binary"""
    print("looking for releases")
    if "assets" in tag and "browser_download_url" in tag["assets"][0]:
        link = tag["assets"][0]["browser_download_url"]
    return link


def configure_autoupdater():
    addon_updater_ops.register(bl_info)
    addon_updater_ops.updater.select_link = select_zip_file
    addon_updater_ops.updater.use_releases = True
    addon_updater_ops.updater.remove_pre_update_patterns = ["*.py", "*.pyc", "*.xml", "*.exe", "*.rst", "VERSION", "*.xsd"]
    addon_updater_ops.updater.user = "niftools"
    addon_updater_ops.updater.repo = "blender_niftools_addon"
    addon_updater_ops.updater.website = "https://github.com/niftools/blender-niftools-addon/"
    addon_updater_ops.updater.version_min_update = (0, 0, 2)


def unregister():
    # addon updater unregister
    addon_updater_ops.unregister()

    # no idea how to do this... oh well, let's not lose any sleep over it uninit_loggers()
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
