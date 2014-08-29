from . import armature, collision, geometry, object, shader

def register():
    armature.register()
    collision.register()
    geometry.register()
    object.register()
    shader.register()
    
def unregister():
    armature.unregister()
    collision.unregister()
    geometry.unregister()
    object.unregister()
    shader.unregister()