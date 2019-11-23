""" Nif User Interface, connect custom properties from properties.py into Blenders UI"""

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


class CollisionBoundsPanel(Panel):
    bl_label = "Collision Bounds"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "physics"
    '''
    @classmethod
    def poll(cls, context):
    '''

    def draw_header(self, context):
        game = context.active_object.game
        self.layout.prop(game, "use_collision_bounds", text="")

    def draw(self, context):
        layout = self.layout

        game = context.active_object.game
        col_setting = context.active_object.nifcollision

        layout.active = game.use_collision_bounds
        layout.prop(game, "collision_bounds_type", text="Bounds Type")
        layout.prop(game, "radius", text="Radius")
        layout.prop(game, "velocity_max", text="Velocity Max")

        box = layout.box()
        box.active = game.use_collision_bounds

        box.prop(col_setting, "col_filter", text='Col Filter')  # col filter prop
        box.prop(col_setting, "deactivator_type", text='Deactivator Type')  # motion dactivation prop
        box.prop(col_setting, "solver_deactivation", text='Solver Deactivator')  # motion dactivation prop
        box.prop(col_setting, "quality_type", text='Quality Type')  # quality type prop
        box.prop(col_setting, "oblivion_layer", text='Oblivion Layer')  # oblivion layer prop
        box.prop(col_setting, "max_linear_velocity", text='Max Linear Velocity')  # oblivion layer prop
        box.prop(col_setting, "max_angular_velocity", text='Max Angular Velocity')  # oblivion layer prop
        box.prop(col_setting, "motion_system", text='Motion System')  # motion system prop
        box.prop(col_setting, "havok_material", text='Havok Material')  # havok material prop
        box.prop(col_setting, "skyrim_havok_material", text='Skyrim Havok Material')  # havok material prop

        con_setting = context.active_object.niftools_constraint

        box.prop(con_setting, "LHMaxFriction", text='LHMaxFriction')
        box.prop(con_setting, "tau", text='tau')
        box.prop(con_setting, "damping", text='Damping')
