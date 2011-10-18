Design Issues
=============

This document lists some conventions, along with a few non-trivial
issues while porting the scripts from the Blender 2.4x API to the
2.5x+ API.

Porting Strategy
----------------

We are following the following strategy for porting the scripts:

1. Write regression test for desired feature.
2. Run the test.
3. Fix the first exception that occurs, and commit the fix.
4. Go back to step 2 until no more exceptions are raised.
5. Do the next 2.6.x release.
6. Listen to feedback from users, and go back to step 1.

The 2.6.x series is designated as purely experimental.

Once enough features have and pass their regression test---i.e. as
soon as the new scripts can be considered en par with the old
scripts---the code will be refactored and cleaned up, possibly moving
some bits out to seperate addons (hull script, morph copy, etc.). The
refactor is reserved for the 3.x.x series.

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
  * ``n_obj`` for a generic
    :class:`pyffi.formats.nif.NifFormat.NiObject`
  * ``n_geom`` for a :class:`pyffi.formats.nif.NifFormat.NiGeometry`

.. todo::

   These conventions are not yet consistently applied in the
   code. Stick to it for new code, but we are holding off a rename for
   the planned 3.x.x refactor.

Differences Between Blender 2.4x and 2.5x
-----------------------------------------

* Beware that, unlike in blender 2.4x, :attr:`bpy.types.MeshFace.vertices` is
  *not* a list of the type :class:`bpy.types.MeshVertex`, but are :class:`int`\ s
  mapping into :attr:`bpy.types.Mesh.vertices`, so you need for instance::

      (b_mesh.vertices[b_vertex_index].co for b_vertex_index in b_face.vertices)

  when requiring the actual vertex coordinates of a
  :class:`bpy.types.MeshFace`.

* Ipo's are gone. They are replaced by
  :attr:`bpy.types.Object.animation_data` (see :class:`bpy.types.AnimData`).

* Vertex groups are accessible via
  :attr:`bpy.types.Object.vertex_groups`, instead of via
  :class:`bpy.types.Mesh`.

* Beware of the difference between :attr:`bpy.types.Object.draw_bounds_type`
  and :attr:`bpy.types.GameObjectSettings.collision_bounds_type` (accessible via
  :attr:`bpy.types.Object.game`):

  - There is no ``'CONVEX_HULL'`` :attr:`bpy.types.Object.draw_bounds_type`.

  - To identify the collision type to export, we rely exclusively on
    :attr:`bpy.types.GameObjectSettings.collision_bounds_type`.
    This also ensures that collision settings imported from nifs
    will work with blender's game engine.

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

.. _dev-design-error-reporting:

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

* What is the difference between :attr:`bpy.types.MeshFace.vertices`
  and :attr:`bpy.types.MeshFace.vertices_raw`?

* What is the difference between ``'CAPSULE'`` and ``'CYLINDER'``
  :attr:`bpy.types.Object.draw_bounds_type`\ s
  (and similar for
  :attr:`bpy.types.GameObjectSettings.collision_bounds_type`)?
  We are using
  ``'CYLINDER'`` at the moment because ``'CAPSULE'`` is lacking
  visualisation.

* How do you get the set of all vertices in a :class:`bpy.types.VertexGroup`?
