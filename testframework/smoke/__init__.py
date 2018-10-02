import nose

import bpy
import addon_utils    


class TestSmokeTests:

    nif_module_name = "io_scene_nif"

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
            import io_scene_nif
        except ImportError:
            print("Failed to import io_scene_nif module")
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
