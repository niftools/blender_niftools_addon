from . import armature, collision, geometry, material, object, shader

def register():
    armature.register()
    collision.register()
    geometry.register()
    material.register()
    object.register()
    shader.register()
    
def unregister():
    armature.unregister()
    collision.unregister()
    geometry.unregister()
    material.unregister()
    object.unregister()
    shader.unregister()