"""Feature documentation."""

import bpy
import nose.tools
import test

class TestFeature(test.subfeatures):
    def b_create_object(self):
        """Create blender objects in current blender scene for feature."""
        raise NotImplementedError

    def b_check_object(self, b_obj):
        """Check blender object against feature."""
        raise NotImplementedError

    def n_check_data(self, n_data):
        """Check nif data against feature."""
        raise NotImplementedError
