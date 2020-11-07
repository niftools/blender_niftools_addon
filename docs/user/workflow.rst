.. _user-workflow:

========
Workflow
========

This section explains vthe general workflow used to import and export
``.nif`` files using Blender.

* The nif importer and exporters are available in **File** > **Import** and
  **File** > **Export**, repsectively.

.. note::
   If you need an introduction consider reading `the Blender Manual
   <https://blender.org/manual/>`_. The documentation below assumes that you
   have at least beginner level skills with Blender.

.. _user-workflow-import:

------
Import
------

You now can import the nif directly into Blender! These settings are
explained at :ref:`I/O Settings Section <user-features-iosettings-import>`.

.. _user-workflow-export:

------
Export
------

The following section deals the various model components, required to export
3D objects to the ``.nif`` format.

+-----------------------------------+-----------------------------------------+
|              Section              |               Description               |
+===================================+=========================================+
| :ref:`Base Model <geometry-mesh>` | Create your base model and configure    |
|                                   | configure the object's settings         |
+-----------------------------------+-----------------------------------------+
| :ref:`Nif Info <object-common>`   | Add in the required general information |
|                                   | to identify the ``.nif`` file           |
+-----------------------------------+-----------------------------------------+
| :ref:`Shaders <shader>`           | Create and configure shaders for each   |
|                                   | selected object                         |
+-----------------------------------+-----------------------------------------+
| :ref:`Materials <properties>`     | Create and configure materials for each |
|                                   | selected object                         |
+-----------------------------------+-----------------------------------------+
| :ref:`Textures <textures>`        | Add different texture types for each    |
|                                   | material                                |
+-----------------------------------+-----------------------------------------+
| :ref:`Exporting <iosettings>`     | Now you're ready for export! Check the  |
|                                   | link to learn about all of the export   |
|                                   | settings!                               |
+-----------------------------------+-----------------------------------------+

.. _workflow-advmesh:

-----------------
Advanced Modeling
-----------------

The following are advanced topics and optional for *most* models.
You should only attempt the following when you are comfortable with the basics.

+---------------------------------------+-------------------------------------+
|                Section                |             Description             |
+=======================================+=====================================+
| :ref:`Collisions <collision-system>`  | Create collision objects and update |
|                                       | their collision settings            |
+---------------------------------------+-------------------------------------+
| :ref:`Armatures <armature-armatures>` | Create a rigged model and configure |
|                                       | the flags for each selected bone    |
+---------------------------------------+-------------------------------------+
| :ref:`Animations <#>`                 | Currently Unsupported               |
+---------------------------------------+-------------------------------------+
