Naming Conventions
------------------

.. _development-design-conventions:

* Stick to the official Python style guide (`PEP 8
  <http://www.python.org/dev/peps/pep-0008/>`_).
  
* Instances of Blender classes start with ``b_`` whilst instances of
  nif classes start with ``n_``. Examples:

  * ``n_obj`` for a generic :class:`pyffi.formats.nif.NifFormat.NiObject`
  * ``n_geom`` for a :class:`pyffi.formats.nif.NifFormat.NiGeometry`
  * ``b_mesh`` for a Blender :class:`bpy.types.Mesh`
  * ``b_face`` for a Blender :class:`bpy.types.MeshFace`
  * ``b_vertex`` for a Blender :class:`bpy.types.MeshVertex`
  * ``b_vector`` for a Blender :class:`mathutils.Vector`
  * ``b_obj`` for a Blender :class:`bpy.types.Object`
  * ``b_mat`` for a Blender :class:`bpy.types.Material`
  * ``b_bone`` for a Blender :class:`bpy.types.Bone`

.. todo::

   These conventions are not yet consistently applied in the code. 