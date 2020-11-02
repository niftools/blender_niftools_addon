"""Module for regression testing that the Blender Niftools Addon installs and enables correctly"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2011, NIF File Format Library and Tools contributors.
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

import nose

import bpy
import addon_utils    


class TestSmokeTests:

    nif_module_name = "io_scene_niftools"

    def test_ordered_test(self):
        if self.is_enabled():
            self._disable_addon()
        self._enable_addon()
        self._disable_addon()

    def _enable_addon(self):
        """Enables the nif scripts addon, so all tests can use it."""
        addon_utils.enable(module_name=self.nif_module_name, default_set=True, persistent=False, handle_error=None)
        nose.tools.assert_true(self.is_enabled())
        print("Addon enabled successfully")
        try:
            import io_scene_niftools
        except ImportError:
            print("Failed to import io_scene_niftools module")
            assert False
        try:
            import pyffi
        except ImportError:
            print("Dependancy was not found, ensure that pyffi was built and included with the installer")
            assert False

    def _disable_addon(self):
        """Disables the nif scripts addon, so all tests can use it."""
        addon_utils.disable(module_name=self.nif_module_name, default_set=True, handle_error=None)
        nose.tools.assert_false(self.is_enabled())

    def is_enabled(self):
        return self.nif_module_name in bpy.context.user_preferences.addons.keys()
