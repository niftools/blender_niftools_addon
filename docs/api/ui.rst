User Interface
==============

* The user first activates the addon via **File > User Preferences > Addons**.  
* This triggers the :func:`~io_scene_nif.register` function, which adds the :class:`~io_scene_nif.ui.NifImportUI` and :class:`~io_scene_nif.ui.NifExportUI` operators to the **File > Import** and **File > Export** menus.
* These operators are integrated within the user interface, and their responsibility is to allow the user to configure the import and export properties. 
* They delegate the actual import and export to the :class:`~io_scene_nif.nif_import.NifImport` and :class:`~io_scene_nif.nif_export.NifExport` classes.

.. module:: io_scene_nif

.. autodata:: bl_info

.. autofunction:: menu_func_import

.. autofunction:: menu_func_export

.. autofunction:: register

.. autofunction:: unregister