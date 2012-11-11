Design Issues
=============

This document lists some conventions, along with a few non-trivial
issues while porting the plugin from the Blender 2.4x API to the
2.6x+ API.

Porting Strategy
----------------

We are following the following strategy for porting the plugin:

#. Write regression test for desired feature.
#. Run the test.
#. Fix the first exception that occurs, and commit the fix.
#. Go back to step 2 until no more exceptions are raised.
#. Do the next 2.6.x release.
#. Listen to feedback from users, and go back to step 1.

The 2.6.x series is designated as purely experimental.

Once enough features have and pass their regression test---i.e. as
soon as the new plugin can be considered en par with the old
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
  * ``n_obj`` for a generic :class:`pyffi.formats.nif.NifFormat.NiObject`
  * ``n_geom`` for a :class:`pyffi.formats.nif.NifFormat.NiGeometry`

.. todo::

   These conventions are not yet consistently applied in the
   code. Stick to it for new code, but we are holding off a rename for
   the planned 3.x.x refactor.

Strings and Bytes
-----------------

Generally, we use :class:`str` everywhere, and convert :class:`bytes`
to :class:`str` whenever interfacing directly with the nif data.

.. todo::

   Add an encoding import/export option.

Regression Tests
----------------

Ideally, for every feature, first, a regression test should be
written. Ideally, the following process is followed:

#. Create a new python file to contain the feature regression test
   code. For example, if the feature concerns *blabla*, the test case
   would be stored in ``testframework/test/test_blabla.py``.
   Derive the test class from
   :class:`test.SingleNif`, and name it :class:`TestBlabla`.

   .. NOTE template is in flux, removed for the time being
   .. Use the template available in ``testframework/test/template.py``.


#. Create a new text file ``docs/features/blabla.rst`` to contain the
   feature user documentation,
   and add it to the table of contents in ``docs/features/index.rst``.
   If there are particular issues with the
   feature's implementation, make a note of it in
   ``docs/development/design.rst``.

#. Write feature test data and test code on nif level:

   - Create a nif (say in nifskope, or with the old blender nif
     scripts).
     Take care to make the file as small as possible.
     Stick to minimal geometry.

   - Use pyffi's ``dump_python`` spell to convert it to python code.
     Store the relevant parts of the code
     in ``testframework/test/gen_blablabla.py``.
     The :meth:`n_create_data` method of the test class
     then uses the :mod:`gen_blablabla` module
     to construct the nif data.

     .. note::

        We split creation code from the rest of the test code
        to keep the test class size manageable.
        If the Python code for creating the nif is very small, it could
        be directly included in :meth:`n_create_data`.

   - Write Python code which test the nif against the desired feature.
     This code goes in the :meth:`n_check_data` method of the test class.

#. Write feature test code on blender level:

   - Write Python code which create the corresponding blender scene.
     Where possible make the test case as simple as possible. For
     instance, use primitives readily available in blender. This code
     goes in the :meth:`b_create_objects` method of the test class.

   - Document the feature in ``docs/features/blabla.rst`` as you write
     :meth:`b_create_objects`: explain what the user has to do in blender in order
     to export the desired data, and where in blender the data ends up
     on import.

   - Write Python code which test the blender scene against the
     desired feature: :meth:`b_check_data` method of the test class.

#. Now implement the feature in the import and export plugin, until
   the regression test passes.

That's it!

The tests will actually do the following:

#. Test that import-export works as expected:

   - Call :meth:`n_check_data` on test nif.

   - Import the nif ``test/nif/blabla0.nif`` and call :meth:`b_check_data` on
     imported scene.

   - Export the nif to ``test/nif/blabla1.nif`` call :meth:`n_check_data` on
     exported data.

#. Test that export-import works as expected:

   - Call :meth:`b_create_objects` to create the scene,
     and :meth:`b_check_data` to check it.

   - Export the nif to ``test/nif/blabla2.nif`` and call
     :meth:`n_check_data` on exported nif.

   - Clear blender scene, import the exported nif, and call
     :meth:`b_check_data` on imported scene.

This ensures data integrity both at Blender level and at nif level.

.. generate, and link to, test API documentation?

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
  
- vertices is a collection, accessible in the form vertices.co[0] -> 7
- vertices_raw returns a list of values -> (7,2,0)

* What is the difference between ``'CAPSULE'`` and ``'CYLINDER'``
  :attr:`bpy.types.Object.draw_bounds_type`\ s
  (and similar for
  :attr:`bpy.types.GameObjectSettings.collision_bounds_type`)?
  We are using
  ``'CYLINDER'`` at the moment because ``'CAPSULE'`` is lacking
  visualisation.

* How do you get the set of all vertices in a :class:`bpy.types.VertexGroup`?
