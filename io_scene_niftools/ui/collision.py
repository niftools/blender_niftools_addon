"""Nif User Interface, connect custom collision properties from properties.py into Blenders UI"""

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2014, NIF File Format Library and Tools contributors.
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


class CollisionBoundsPanel(Panel):
    bl_idname = "NIFTOOLS_PT_CollisionBoundsPanel"
    bl_label = "Niftools Collision Bounds"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"

    @classmethod
    def poll(cls, context):
        if context.active_object.rigid_body:
            return True
        return False

    def draw(self, context):
        layout = self.layout

        col_setting = context.active_object.nifcollision

        box = layout.box()
        box.prop(col_setting, "col_filter", text='Col Filter')  # col filter prop
        box.prop(col_setting, "deactivator_type", text='Deactivator Type')  # motion deactivation prop
        box.prop(col_setting, "solver_deactivation", text='Solver Deactivator')  # motion deactivation prop
        box.prop(col_setting, "quality_type", text='Quality Type')  # quality type prop
        box.prop(col_setting, "oblivion_layer", text='Oblivion Layer')  # oblivion layer prop
        box.prop(col_setting, "max_linear_velocity", text='Max Linear Velocity')  # oblivion layer prop
        box.prop(col_setting, "max_angular_velocity", text='Max Angular Velocity')  # oblivion layer prop
        box.prop(col_setting, "motion_system", text='Motion System')  # motion system prop


classes = [
    CollisionBoundsPanel
]


def register():
    register_classes(classes, __name__)


def unregister():
    unregister_classes(classes, __name__)
