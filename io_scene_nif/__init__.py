"""Blender Plug-in for Nif import and export."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2011, NIF File Format Library and Tools contributors.
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

#: Blender addon info.
bl_info = {
    "name": "NetImmerse/Gamebryo nif format",
    "description":
    "Import and export files in the NetImmerse/Gamebryo nif format (.nif)",
    "author": "NifTools Team",
    "version": (2, 6, 0), # can't read from VERSION, blender wants it hardcoded
    "blender": (2, 7, 1),
    "api": 39257,
    "location": "File > Import-Export",
    "warning": "partially functional, port from 2.49 series still in progress",
    "wiki_url": (
        "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/"\
        "Import-Export/Nif"),
    "tracker_url": (
        "http://sourceforge.net/tracker/?group_id=149157&atid=776343"),
    "support": "COMMUNITY",
    "category": "Import-Export"}

import io_scene_nif

try:
    from io_scene_nif import nif_debug
    nif_debug.startdebug()
except:
    print("Failed to load debug module")

import sys
import os

# Python dependencies are bundled inside the io_scene_nif/modules folder
_modules_path = os.path.join(os.path.dirname(__file__), "modules")
if not _modules_path in sys.path:
    sys.path.append(_modules_path)
del _modules_path

from io_scene_nif import properties, operators, operator, ui

import bpy
import bpy.props

import logging

def _init_loggers():
    """Set up loggers."""
    niftoolslogger = logging.getLogger("niftools")
    niftoolslogger.setLevel(logging.WARNING)
    pyffilogger = logging.getLogger("pyffi")
    pyffilogger.setLevel(logging.WARNING)
    loghandler = logging.StreamHandler()
    loghandler.setLevel(logging.DEBUG)
    logformatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
    loghandler.setFormatter(logformatter)
    niftoolslogger.addHandler(loghandler)
    pyffilogger.addHandler(loghandler)


def menu_func_import(self, context):
    self.layout.operator(
        operators.NifImportOperator.bl_idname, text="NetImmerse/Gamebryo (.nif)")


def menu_func_export(self, context):
    self.layout.operator(
        operators.NifExportOperator.bl_idname, text="NetImmerse/Gamebryo (.nif)")


def register():
    _init_loggers()
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    # no idea how to do this... oh well, let's not lose any sleep over it
    #_uninit_loggers()
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_module(__name__)
    

if __name__ == "__main__":
    register()
