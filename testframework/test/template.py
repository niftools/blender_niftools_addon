"""Feature documentation."""

import bpy
import nose.tools
import test

class TestFeature(SingleNif):
    """Test Feature"""
    
    n_name = ''
    # location the nif will be created in
    
    b_name = ''
    # name of blender object
    
    def b_create_objects(self):
        """Create blender objects in current blender scene for feature."""
        # call sub_methods for reusability
        raise NotImplementedError

    def b_check_data(self, b_obj):
        """Check blender object against feature."""
        # call sub_methods for reusability
        raise NotImplementedError

    def n_create_data(self):
        """Create nif using python code"""
        # create the nif in feature blocks
        raise NotImplementedError
        
    def n_check_data(self):
        """Check nif data against feature."""
        # check feature, reuse other feature tests where possible
        raise NotImplementedError
