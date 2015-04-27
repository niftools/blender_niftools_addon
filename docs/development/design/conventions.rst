Naming Conventions
------------------

* Stick to the official Python style guide (`PEP 8
  <http://www.python.org/dev/peps/pep-0008/>`_).
  
* Instances of blender classes start with ``b_`` whilst instances of
  nif classes start with ``n_``. Examples:

  * ``b_mesh`` for a blender :class:`bpy.types.Mesh`
  * ``b_face`` for a blender :class:`bpy.types.MeshFace`
  * ``b_vertex`` for a blender :class:`bpy.types.MeshVertex`
  * ``b_vector`` for a blender :class:`mathutils.Vector`
  * ``b_obj`` for a blender :class:`bpy.types.Object`
  * ``b_mat`` for a blender :class:`bpy.types.Material`
  * ``b_bone`` for a blender :class:`bpy.types.Bone`
  * ``n_obj`` for a generic :class:`pyffi.formats.nif.NifFormat.NiObject`
  * ``n_geom`` for a :class:`pyffi.formats.nif.NifFormat.NiGeometry`

.. TODO:

   These conventions are not yet consistently applied in the code. 