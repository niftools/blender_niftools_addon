"""Nif User Interface, custom nif properties for geometry"""

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
                       CollectionProperty,
                       IntProperty,
                       BoolProperty,
                       )
from bpy.types import PropertyGroup

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class SkinPartHeader(PropertyGroup):
    pf_partcount: IntProperty(
        name='Partition count',
        min=0,
        default=0
    )


class SkinPartFlags(PropertyGroup):
    name: bpy.props.StringProperty(
        name='name',
        default=''
    )

    pf_startflag: BoolProperty(
        name='Start Net Boneset'
    )

    pf_editorflag: BoolProperty(
        name="Editor Visible"
    )


CLASSES = [
    SkinPartHeader,
    SkinPartFlags
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.Object.niftools_part_flags = bpy.props.CollectionProperty(type=SkinPartFlags)
    bpy.types.Object.niftools_part_flags_panel = bpy.props.PointerProperty(type=SkinPartHeader)


def unregister():
    del bpy.types.Object.niftools_part_flags
    del bpy.types.Object.niftools_part_flags_panel

    unregister_classes(CLASSES, __name__)
