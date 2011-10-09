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
  * ``b_vert`` for a blender :class:`bpy.types.MeshVertex`
  * ``b_vector`` for a blender :class:`mathutils.Vector`
  * ``b_obj`` for a blender :class:`bpy.types.Object`
  * ``n_obj`` for a generic
    :class:`pyffi.formats.nif.NifFormat.NiObject`
  * ``n_geom`` for a :class:`pyffi.formats.nif.NifFormat.NiGeometry`

.. todo::

   These conventions are not yet consistently applied in the
   code. Stick to it for new code, but we are holding off a rename for
   the planned 3.x.x refactor.

Face Vertices
-------------

Beware that, unlike in blender 2.4x, :class:`MeshFace.vertices` is
*not* a list of the type :class:`MeshVertex`, but are :class:`int`\ s
mapping into :class:`Mesh.vertices`, so you need for instance::

    (b_mesh.vertices[b_vert_index].co for b_vert_index in b_face)

when requiring the actual vertex coordinates of a
:class:`bpy.types.MeshFace`.

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
