"""Nif Format Properties, stores custom nif properties for armature settings"""

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

import bpy
from bpy.props import (PointerProperty,
                       IntProperty,
                       EnumProperty,
                       StringProperty
                       )
from bpy.types import PropertyGroup


class BoneProperty(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Bone.niftools = PointerProperty(
            name='Niftools Bone Property',
            description='Additional bone properties used by the Nif File Format',
            type=cls,
        )
        cls.boneflags = IntProperty(
            name='Bone Flag',
            default=0
        )
        cls.bonepriority = IntProperty(
            name='Bone Priority',
            default=0
        )
        cls.longname = StringProperty(
            name='Nif Long Name'
        )

    @classmethod
    def unregister(cls):
        del bpy.types.Bone.niftools

class ArmatureProperty(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Armature.niftools = PointerProperty(
            name='Niftools Armature Property',
            description='Additional armature properties used by the Nif File Format',
            type=cls,
        )

        cls.axis_forward = EnumProperty(
                name="Forward",
                items=(('X', "X Forward", ""),
                       ('Y', "Y Forward", ""),
                       ('Z', "Z Forward", ""),
                       ('-X', "-X Forward", ""),
                       ('-Y', "-Y Forward", ""),
                       ('-Z', "-Z Forward", ""),
                       ),
                default="X",
                )

        cls.axis_up = EnumProperty(
                name="Up",
                items=(('X', "X Up", ""),
                       ('Y', "Y Up", ""),
                       ('Z', "Z Up", ""),
                       ('-X', "-X Up", ""),
                       ('-Y', "-Y Up", ""),
                       ('-Z', "-Z Up", ""),
                       ),
                default="Y",
                )

    @classmethod
    def unregister(cls):
        del bpy.types.Armature.niftools
