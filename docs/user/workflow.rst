.. _user-workflow:

Workflow
========

This section will explain the general workflow used to import/export .nif files to/from blender.

* The nif importer and exporter is show under 
   **File > Import** and **File > Export**.

.. note::
   This assumes at least begginer level skills with blender.
   If you need an introduction consider reading `the Blender Manual <https://http://blender.org/manual/>`_.

.. _user-workflow-import:

Import
------

You now can import the nif directly into blender! 
These settings are explained at :ref:`I/O Settings Section <user-features-iosettings-import>`.

.. _user-workflow-export:

Export
------

The following section deals the various model components, required to export to the .nif format.

+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Base Model**         | Create your base model and configure the settings on the object, refer to the :ref:`Geometry Section <geometry-mesh>`.    |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **General Nif Info**   | Add in the general info required to identify the .nif file, refer to the :ref:`Nif Version Info <object-common>`.         |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Shaders**            | Create and configure the shaders for each selected object, refer to the :ref:`Shader Section <shader>`.                   |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Material**           | Create and configure the materials for each selected object, refer to the :ref:`Materials Section <properties>`.          |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Textures**           | Add the different textures types for each material, refer to the :ref:`Textures Section <textures>`.                      |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Exporting**          | You're now ready to export! These settings are explained at :ref:`I/O Settings Section <iosettings>`.                     |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+


.. _workflow-advmesh:

Advanced Modeling
-----------------

The following are advanced topics and optional for most models.
You should only attempt the following when you are compentent in the basics.

+----------------+----------------------------------------------------------------------------------------------------------------------------------+
| **Collisions** | Create collision objects and update their collision settings, refer to the :ref:`Collision Section <collison-system>`.           |
+----------------+----------------------------------------------------------------------------------------------------------------------------------+
| **Armatures**  | Create a rigged model and configure the flags for each selected bone, refer to the :ref:`Armature Section <armature-armatures>`. |
+----------------+----------------------------------------------------------------------------------------------------------------------------------+
| **Animations** | Not yet supported.                                                                                                               |
+----------------+----------------------------------------------------------------------------------------------------------------------------------+

