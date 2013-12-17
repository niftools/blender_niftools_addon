import nose

import bpy
import addon_utils    
nif_module_name = "io_scene_nif"

def test_enable_addon():
    """Enables the nif scripts addon, so all tests can use it."""
    try:
        addon_utils.enable(module_name=nif_module_name, default_set=True, persistent=False, handle_error=None)
    except:
        pass
    
    enabled = False
    modules = bpy.context.user_preferences.addons.keys()
    if(nif_module_name in modules):
        enabled = True
        
    nose.tools.assert_true(enabled)
    
    
def test_dependancies():
    try:
        import pyffi
    except:
        print("Dependancy was not found, ensure that pyffi was built and included with the installer")
        assert(False)
    
    
def test_disable_addon():
    """Disables the nif scripts addon, so all tests can use it."""
    
    enabled = False
    if(nif_module_name in bpy.context.user_preferences.addons.keys()):
        enabled = True

    nose.tools.assert_true(enabled)
    
    try:
        addon_utils.disable(module_name=nif_module_name, default_set=True, handle_error=None)
    except:
        pass
    
    disabled = False
    modules = bpy.context.user_preferences.addons.keys()
    if(nif_module_name not in modules):
        disabled = True
        
    nose.tools.assert_true(disabled)