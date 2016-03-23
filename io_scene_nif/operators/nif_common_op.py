'''Blender operators, functions called through menus'''

# ***** BEGIN LICENSE BLOCK *****
# 
# Copyright © 2005-2013, NIF File Format Library and Tools contributors.
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

class NifOperatorCommon:
    """Abstract base class for import and export user interface."""

    # filepath is created by ImportHelper/ExportHelper

    #: Default file name extension.
    filename_ext = ".nif"

    #: File name filter for file select dialog.
    filter_glob = bpy.props.StringProperty(
        default="*.nif;*.item;*.nifcache;*.jmi", options={'HIDDEN'})

    #: Level of verbosity on the console.
    log_level = bpy.props.EnumProperty(
        items=(
            ("DEBUG", "Debug",
             "Show all messages (only useful for debugging)."),
            ("INFO", "Info",
             "Show some informative messages, warnings, and errors."),
            ("WARNING", "Warning",
             "Only show warnings and errors."),
            ("ERROR", "Error",
             "Only show errors."),
            ("CRITICAL", "Critical",
             "Only show extremely critical errors."),
            ),
        name="Log Level",
        description="Level of verbosity on the console.",
        default="WARNING")

    #: Name of file where Python profiler dumps the profile.
    profile_path = bpy.props.StringProperty(
        name="Profile Path",
        description="File where Python profiler dumps the profile. Set to empty string to turn off profiling.",
        maxlen=1024,
        default="",
        subtype="FILE_PATH",
        options={'HIDDEN'})

    #: Used for checking equality between floats.
    epsilon = bpy.props.FloatProperty(
        name="Epsilon",
        description="Used for checking equality between floats.",
        default=0.0005,
        min=0.0, max=1.0, precision=5,
        options={'HIDDEN'})


