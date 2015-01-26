Workflow
--------

This section will explain the general workflow used to import/export .nif files to/from blender.
If you need an introduction to blender consider reading `the Blender Manual <https://http://blender.org/manual/>`_.

.. toctree::
   :maxdepth: 1
   
   workflow
   
   
General Workflow
================
.. _workflow:



.. Note::
   This assumes at least begginer level skills with blender.


Import
------
.. _workflow-import:

What should be added here? Settings on import? Possibly not needed since the settings are already discussed in iosettings

Export
------
.. _workflow-export:

Now we'll deal with all the steps needed to export your .nif file.

* Create your base model;
* Configure nif versions and general flags;
* Configure your materials;
* Configure your textures & shaders;
* Export with the correct settings.

Base Model
.. _workflow-basemesh:

Configure the settings on the object, refer to the :ref:`Geometry Section <geometry-mesh>`.


General Nif Info
.. _workflow-geninfo:

Add in the general info required to identify the .nif file, refer to the :ref: `Nif Version Info <object-common-version>`.


Material & Shaders
.. _workflow-materials:

Configure the materials for each selected object, refer to the :ref:`Materials Section <properties>`.

Textures
.. _workflow-textures:

Configure the textures for each selected object, refer to the :ref:`Textures Section <textures>`.

Exporting
.. _workflow-exportexport:

You're now ready to export! These settings are explained at :ref:`I/O Settings Section <iosettings>`.
 
Advanced Modeling
-----------------

#. Collisions
.. _workflow-collision:

Add in collision for each selected object, refer to the :ref:`Collision Section <collison-system>`.

#. Armatures
.. _workflow-boneflag:

Configure the flags for each selected bone, refer to the :ref:`Armature Section <armature-armatures>`. If you don't have an armature you can skip this step.



   