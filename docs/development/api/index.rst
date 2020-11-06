=================
API Documentation
=================

.. _development-api:

The following document contains a high-level overview of components and submodules.
The sub-module documentation is generated automatically using Sphinx.

Contents:

.. toctree::
   :maxdepth: 1

   submodules/modules
   
   
--------------
User Interface
--------------

* The user first activates the addon via **File > User Preferences > Addons**.  
* This triggers the :func:`~io_scene_niftools.register` function, which adds the :class:`~io_scene_niftools.ui.NifImportUI` and :class:`~io_scene_niftools.ui.NifExportUI` operators to the **File > Import** and **File > Export** menus.
* These operators are integrated within the user interface, and their responsibility is to allow the user to configure the import and export properties. 
* They delegate the actual import and export to the :class:`~io_scene_niftools.nif_import.NifImport` and :class:`~io_scene_niftools.nif_export.NifExport` classes.



------------------
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
