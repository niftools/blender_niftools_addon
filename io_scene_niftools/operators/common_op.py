"""Blender operators, functions called through menus"""

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
import bpy


class CommonDevOperator:
    """Abstract base class for import and export user interface."""

    error_level_map = (
        ("DEBUG", "Debug", "Show all messages (only useful for debugging).", 10),
        ("INFO", "Info", "Show some informative messages, warnings, and errors.", 20),
        ("WARNING", "Warning", "Only show warnings and errors.", 30),
        ("ERROR", "Error", "Only show errors.", 40),
        ("CRITICAL", "Critical", "Only show extremely critical errors.", 50),
    )

    # Level of verbosity on the console.
    plugin_log_level: bpy.props.EnumProperty(
        items=error_level_map,
        name="Plugin Log Level",
        description="Blender Nif Plugin log level of verbosity on the console.",
        default="INFO")

    # Level of verbosity on the console.
    pyffi_log_level: bpy.props.EnumProperty(
        items=error_level_map,
        name="Pyffi Log Level",
        description="Pyffi log level of verbosity on the console.",
        default="INFO")

    # Name of file where Python profiler dumps the profile.
    profile_path: bpy.props.StringProperty(
        name="Profile Path",
        description="File where Python profiler dumps the profile. Set to empty string to turn off profiling.",
        maxlen=1024,
        default="",
        subtype="FILE_PATH",
        options={'HIDDEN'})

    # Used for checking equality between floats.
    epsilon: bpy.props.FloatProperty(
        name="Epsilon",
        description="Used for checking equality between floats.",
        default=0.0005,
        min=0.0, max=1.0, precision=5,
        options={'HIDDEN'})


class CommonScale:

    def get_import_scale(self):
        return bpy.context.scene.niftools_scene.scale_correction

    def set_import_scale(self, scale):
        bpy.context.scene.niftools_scene.scale_correction = scale

    # Number of nif units per blender unit.
    scale_correction: bpy.props.FloatProperty(
        name="Scale Correction",
        description="Changes size of mesh to fit onto Blender's default grid.",
        get=get_import_scale,
        set=set_import_scale,
        default=0.1,
        min=0.001, max=100.0, precision=2)


class CommonNif:
    # Default file name extension.
    filename_ext = ".nif"

    # File name filter for file select dialog.
    filter_glob: bpy.props.StringProperty(
        default="*.nif;*.item;*.nifcache;*.jmi",
        options={'HIDDEN'})


class CommonEgm:
    # Default file name extension.
    filename_ext = ".egm"

    # File name filter for file select dialog.
    filter_glob: bpy.props.StringProperty(
        default="*.egm",
        options={'HIDDEN'})


class CommonKf:
    # Default file name extension.
    filename_ext = ".kf"

    # File name filter for file select dialog.
    filter_glob: bpy.props.StringProperty(
        default="*.kf",
        options={'HIDDEN'})
