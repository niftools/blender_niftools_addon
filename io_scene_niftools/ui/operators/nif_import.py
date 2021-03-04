"""Nif User Import custom operator UI Menus"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2015, NIF File Format Library and Tools contributors.
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

from bpy.types import Panel

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class OperatorSetting:
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_parent_id = "FILE_PT_operator"


class OperatorImportIncludePanel(OperatorSetting, Panel):
    bl_label = "Include"
    bl_idname = "NIFTOOLS_PT_import_operator_include"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_nif"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "process")
        layout.prop(operator, "override_scene_info")


class OperatorImportTransformPanel(OperatorSetting, Panel):
    bl_label = "Transform"
    bl_idname = "NIFTOOLS_PT_import_operator_transform"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_nif"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "scale_correction")


class OperatorImportGeometryPanel(OperatorSetting, Panel):
    bl_label = "Transform"
    bl_idname = "NIFTOOLS_PT_import_operator_transform"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_nif"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "combine_vertices")
        layout.prop(operator, "use_custom_normals")


class OperatorImportArmaturePanel(OperatorSetting, Panel):
    bl_label = "Armature"
    bl_idname = "NIFTOOLS_PT_import_operator_armature"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_nif"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "merge_skeleton_roots")
        layout.prop(operator, "send_geoms_to_bind_pos")
        layout.prop(operator, "apply_skin_deformation")


class OperatorImportAnimationPanel(OperatorSetting, Panel):
    bl_options = {'DEFAULT_CLOSED'}

    bl_label = "Animation"
    bl_idname = "NIFTOOLS_PT_import_operator_animation"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_nif"

    def draw_header(self, context):
        sfile = context.space_data
        operator = sfile.active_operator

        self.layout.prop(operator, "animation", text="")

    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation


classes = [
    OperatorImportIncludePanel,
    OperatorImportTransformPanel,
    OperatorImportGeometryPanel,
    OperatorImportArmaturePanel,
    OperatorImportAnimationPanel
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)