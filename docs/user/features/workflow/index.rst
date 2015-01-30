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

You now can import the nif directly into blender! 
These settings are explained at :ref:`I/O Settings Section <iosettings>`.

.. _workflow-export:

Export
------

The following section deals the various model components, required to export to the .nif format.

+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Base Model**         | Create your base model and configure the settings on the object, refer to the :ref:`Geometry Section <geometry-mesh>`.    |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **General Nif Info**   | Add in the general info required to identify the .nif file, refer to the :ref:`Nif Version Info <object-common-version>`. |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Material & Shaders** | Create and configure the materials for each selected object, refer to the :ref:`Materials Section <properties>`.          |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Textures**           | Add the different textures types for each material, refer to the :ref:`Textures Section <textures>`.                      |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+
| **Exporting**          | You're now ready to export! These settings are explained at :ref:`I/O Settings Section <iosettings>`.                     |
+------------------------+---------------------------------------------------------------------------------------------------------------------------+


.. _workflow-advmesh:

Advanced Modeling
-----------------

The following are advanced topics.
You should only attempt the following when you are compentent in the basics.

+----------------+----------------------------------------------------------------------------------------------------------------------------------+
| **Collisions** | Create collision objects and update their collision settings, refer to the :ref:`Collision Section <collison-system>`.           |
+----------------+----------------------------------------------------------------------------------------------------------------------------------+
| **Armatures**  | Create a rigged model and configure the flags for each selected bone, refer to the :ref:`Armature Section <armature-armatures>`. |
+----------------+----------------------------------------------------------------------------------------------------------------------------------+
| **Animations** | Not yet supported                                                                                                                |
+----------------+----------------------------------------------------------------------------------------------------------------------------------+

