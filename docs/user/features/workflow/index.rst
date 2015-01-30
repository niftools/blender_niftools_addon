.. _workflow:

Workflow
========

This section will explain the general workflow used to import/export .nif files to/from blender.


.. Note::
   This assumes at least begginer level skills with blender.
   If you need an introduction consider reading `the Blender Manual <https://http://blender.org/manual/>`_.

.. _workflow-import:

Import
------

You now can import the nif directly into blender! These settings are explained at :ref:`I/O Settings Section <iosettings>`.

.. _workflow-export:

Export
------

Now we'll deal with all the steps needed to export your .nif file.

* Create your base model;
* Configure nif versions and general flags;
* Configure your materials;
* Configure your textures & shaders;
* Export with the correct settings.


**Base Model**

   Configure the settings on the object, refer to the :ref:`Geometry Section <geometry-mesh>`.


**General Nif Info**

   Add in the general info required to identify the .nif file, refer to the :ref:`Nif Version Info <object-common-version>`.


**Material & Shaders**

   Configure the materials for each selected object, refer to the :ref:`Materials Section <properties>`.


**Textures**

   Configure the textures for each selected object, refer to the :ref:`Textures Section <textures>`.


**Exporting**

   You're now ready to export! These settings are explained at :ref:`I/O Settings Section <iosettings>`.

.. _workflow-advmesh:

Advanced Modeling
-----------------

Not all models require collision or have an armature. Here we'll deal with these more advanced topics for your model.


**Collisions**

   Add in collision for each selected object, refer to the :ref:`Collision Section <collison-system>`.


**Armatures**

   Configure the flags for each selected bone, refer to the :ref:`Armature Section <armature-armatures>`.



   