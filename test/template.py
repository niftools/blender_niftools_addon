"""Feature documentation."""

import bpy
import nose.tools
import test

class TestFeature(test.SingleNif):
    def b_create(self):
        """Create blender objects in current blender scene for feature."""
        pass

    def b_check(self):
        """Check current blender scene against feature."""
        pass

    def n_check(self, n_filepath):
        """Check nif file against feature."""
        pass
