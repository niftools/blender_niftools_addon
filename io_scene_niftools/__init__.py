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
import os
import sys
from io_scene_niftools import addon_updater_ops
from io_scene_niftools.utils import logging, debugging
from io_scene_niftools.utils.logging import NifLog
from io_scene_niftools.utils.decorators import register_modules, unregister_modules

# Blender addon info.
bl_info = {
    "name": "NetImmerse/Gamebryo format support",
    "description": "Import and export files in the NetImmerse/Gamebryo formats (.nif, .kf, .egm)",
    "author": "Niftools team",
    "blender": (2, 81, 0),
    "version": (0, 0, 5),  # can't read from VERSION, blender wants it hardcoded
    "api": 39257,
    "location": "File > Import-Export",
    "warning": "Partially functional port from 2.49 series still in progress",
    "wiki_url": "https://blender-niftools-addon.readthedocs.io/",
    "tracker_url": "https://github.com/niftools/blender_niftools_addon/issues",
    "support": "COMMUNITY",
    "category": "Import-Export"
}
global current_dir


def locate_dependencies():
    # Python dependencies are bundled inside the io_scene_nif/dependencies folder
    global current_dir
    current_dir = os.path.dirname(__file__)
    _dependencies_path = os.path.join(current_dir, "dependencies")
    if _dependencies_path not in sys.path:
        sys.path.append(_dependencies_path)
    del _dependencies_path

    with open(os.path.join(current_dir, "VERSION.txt")) as version:
        NifLog.info(f"Loading: Blender Niftools Addon: {version.read()}")
        import pyffi
        NifLog.info(f"Loading: PyFFi: {pyffi.__version__}")


locate_dependencies()
logging.init_loggers()


def retrieve_ordered_submodules():
    from . import properties, operators, ui, update
    return [update, properties, operators, ui]


MODS = retrieve_ordered_submodules()


def register():
    # addon updater code and configurations in case of broken version, try to register the updater first
    # so that users can revert back to a working version
    NifLog.debug("Starting registration")
    configure_autoupdater()

    register_modules(MODS, __name__)


def unregister():
    # addon updater unregister
    unregister_modules(MODS, __name__)
    addon_updater_ops.unregister()


def select_zip_file(self, tag):
    """Select the latest build artifact binary"""
    NifLog.debug("looking for releases")
    if "assets" in tag and "browser_download_url" in tag["assets"][0]:
        link = tag["assets"][0]["browser_download_url"]
    return link


def configure_autoupdater():
    NifLog.debug("Configuring auto-updater")
    addon_updater_ops.register(bl_info)
    addon_updater_ops.updater.select_link = select_zip_file
    addon_updater_ops.updater.use_releases = True
    addon_updater_ops.updater.remove_pre_update_patterns = ["*.py", "*.pyc", "*.xml", "*.exe", "*.rst", "VERSION", "*.xsd"]
    addon_updater_ops.updater.user = "niftools"
    addon_updater_ops.updater.repo = "blender_niftools_addon"
    addon_updater_ops.updater.website = "https://github.com/niftools/blender-niftools-addon/"
    addon_updater_ops.updater.version_min_update = (0, 0, 4)
