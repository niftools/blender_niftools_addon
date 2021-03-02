"""Nif User Interface, connect custom properties from scene.py into Blenders UI"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2016, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class SceneButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"


class ScenePanel(SceneButtonsPanel, Panel):
    bl_label = "Niftools Scene Panel"
    bl_idname = "NIFTOOLS_PT_scene"

    # noinspection PyUnusedLocal
    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        nif_scene_props = context.scene.niftools_scene

        layout = self.layout
        row = layout.column()
        row.prop(nif_scene_props, "game")


class SceneVersionInfoPanel(SceneButtonsPanel, Panel):
    bl_label = "Nif Version Info"
    bl_idname = "NIFTOOLS_PT_scene_version_info"
    bl_parent_id = "NIFTOOLS_PT_scene"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        nif_scene_props = context.scene.niftools_scene
        layout.label(text=NifFormat.HeaderString.version_string(nif_scene_props.nif_version))

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(nif_scene_props, "nif_version")

        col = flow.column()
        col.prop(nif_scene_props, "user_version")

        col = flow.column()
        col.prop(nif_scene_props, "user_version_2")

# class SceneAuthorInfoPanel(SceneButtonsPanel, Panel):
#     bl_label = "Nif Author Info"
#     bl_idname = "NIFTOOLS_PT_scene_author_info"
#     bl_parent_id = "NIFTOOLS_PT_scene"
#
#     def draw(self, context):
#         layout = self.layout
#         layout.use_property_split = True
#
#         nif_scene_props = context.scene.niftools_scene
#
#         flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)
#
#         col = flow.column()
#         col.prop(nif_scene_props, "nif_author_info")
#
#         col = flow.column()
#         col.prop(nif_scene_props, "nif_author_info_2")
#


classes = [
    ScenePanel,
    SceneVersionInfoPanel,
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
