Development Issues
==================

This document lists a few non-trivial issues that we have come across while porting 
the plugin from the Blender 2.4x API to the 2.6x+ API.

Objects
-------

* Vertex groups are accessible via
  :attr:`bpy.types.Object.vertex_groups`, instead of via
  :class:`bpy.types.Mesh`.

Meshes : Index Mapping
----------------------

* Beware that, unlike in blender 2.4x, :attr:`bpy.types.MeshFace.vertices` 
  does not return a list of the type :class:`bpy.types.MeshVertex`.
  Rather :class:`int`\ s are returned which are index values mapping 
  :attr:`bpy.types.MeshFace.vertices` to :attr:`bpy.types.Mesh.vertices`,
  so you need for instance::

      (b_mesh.vertices[b_vertex_index].co for b_vertex_index in b_face.vertices)

  when requiring the actual vertex coordinates of a
  :class:`bpy.types.MeshFace`.
  
  This index mapping is also used by attributes such a vertex color, vertex weight, vertex uv

Meshes
------

* Beware of the **eeekadoodle dance**: if face indices end with a zero
  index, then you have to move that zero index to the front. For
  example (assuming every face is a triangle)::

    faces = [face if face[2] else (face[2], face[0], face[1])
             for face in faces]

  before feeding faces to blender.

* It appears that we have to use
  :meth:`bpy.types.bpy_prop_collection.add` (undocumented) and
  :meth:`bpy.types.bpy_prop_collection.foreach_set` on
  :attr:`bpy.types.Mesh.vertices` and :attr:`bpy.types.Mesh.faces` to
  import vertices and faces::

    from bpy_extras.io_utils import unpack_list, unpack_face_list
    b_mesh.vertices.add(len(verts))
    b_mesh.faces.add(len(faces))
    b_mesh.vertices.foreach_set("co", unpack_list(verts))
    b_mesh.faces.foreach_set("vertices_raw", unpack_face_list(faces))

  After this has been done, uv and vertex
  color layers can be added and imported::

    b_mesh.uv_textures.new()
    for face, b_tface in zip(faces, b_mesh.uv_textures[0].data):
        b_tface.uv1 = uvs[face[0]]
        b_tface.uv2 = uvs[face[1]]
        b_tface.uv3 = uvs[face[2]]

  To import say vertices one by one, use::

     b_mesh.vertices.add(1)
     b_mesh.vertices[-1].co = ...

  .. Note::
      
      This can be improved by batch importing vertices instead of creating verts one by one.

.. _dev-design-error-reporting:

Animation
---------

* Ipo's are gone. They are replaced by
  :attr:`bpy.types.Object.animation_data` (see :class:`bpy.types.AnimData`).

Collision
---------

* Beware of the difference between :attr:`bpy.types.Object.draw_bounds_type`
  and :attr:`bpy.types.GameObjectSettings.collision_bounds_type` (accessible via
  :attr:`bpy.types.Object.game`):

  - There is no ``'CONVEX_HULL'`` :attr:`bpy.types.Object.draw_bounds_type`.

  - To identify the collision type to export, we rely exclusively on
    :attr:`bpy.types.GameObjectSettings.collision_bounds_type`.
    This also ensures that collision settings imported from nifs
    will work with blender's game engine.

Bone
----

* Setting up the parent chile relationship is difficult for a number of reasons

 - The :attr:`bpy.types.Bone.parent` is a read-only value, only writable by through a :class:`bpy.types.EditBone`.
 
 - Assuming that :class:`bpy.types.Bone` 's have been created and added to an  :class:`bpy.types.Armature`
 
 - :class:`bpy.types.EditBone` 's are access via the collection attribute :attr:`bpy.types.Armature.edit_bones`, which only exists while in Edit mode.
 
 - EditBones are accessed through :class:`int` indexed rather :class:`str` index::
 
   b_armatureData.edit_bones[b_child_bone.name].parent = b_armatureData.edit_bones[b_bone.name]


Strings and Bytes
-----------------

Generally, we use :class:`str` everywhere, and convert :class:`bytes`
to :class:`str` whenever interfacing directly with the nif data.

.. todo::

   Add an encoding import/export option.

Error Reporting
---------------

With the older blender 2.4x series, scripts could report fatal errors
simply by raising an exception. The current blender series has the
problem that *exceptions are not passed down to the caller of the
operator*. Apparently, this is because of the way the user interface is
implemented. From a user perspective, this makes no difference,
however, for testing code, this means that **any exceptions raised
cannot be caught by the testing framework**.

The way blender solves this problem goes via the
:meth:`bpy.types.Operator.report` method. So, in your
:meth:`bpy.types.Operator.execute` methods, write::

    if something == is_wrong:
        operator.report({'ERROR'}, 'Something is wrong.')
        return {'FINISHED'}

instead of::

    if something == is_wrong:
        raise RuntimeError('Something is wrong')

When the operator finishes, blender will check for any error reports,
and if it finds any, it will raise an exception, which will be passed
back to the caller. This means that we can no longer raise *specific*
exceptions, but in practice this is not really a problem.

Following this convention makes the operator more user friendly for
other scripts, such as testing frameworks, who might want to catch the
exception and/or inspect error reports.

The :class:`io_scene_nif.import_export_nif.NifImportExport` class has
a dedicated
:meth:`~io_scene_nif.import_export_nif.NifImportExport.error` method
for precisely this purpose.

The list of reports of the last operator execution can be inspected
using :func:`bpy.ops.ui.reports_to_textblock`.

Blender API Mysteries
---------------------

* What is the difference between ``'CAPSULE'`` and ``'CYLINDER'``
  :attr:`bpy.types.Object.draw_bounds_type`\ s
  (and similar for
  :attr:`bpy.types.GameObjectSettings.collision_bounds_type`)?
  We are using
  ``'CYLINDER'`` at the moment because ``'CAPSULE'`` is lacking
  visualisation.

* How do you get the set of all vertices in a :class:`bpy.types.VertexGroup`?

Solved
------

* What is the difference between :attr:`bpy.types.MeshFace.vertices`
  and :attr:`bpy.types.MeshFace.vertices_raw`?
  
- vertices is a collection, accessible in the form vertices.co[0] -> 7
- vertices_raw returns a list of values -> (7,2,0)