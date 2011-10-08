Design Issues
=============

.. _dev-design-error-reporting:

Error Reporting
---------------

With the older blender 2.4x series, scripts could report fatal errors
simply by raising an exception. The current blender series has the
problem that *exceptions are not passed down to the caller of the
operator*. Apparently, this is because the way the user interface is
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
