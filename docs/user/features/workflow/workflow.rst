################
General Workflow
################
.. _workflow:

This section will explain the general workflow used to import/export .nif files to/from blender.

.. NOTE::
   This assumes at least begginer level skills with blender.


Import
======
.. _workflow-import:

***********What should be added here? Settings on import? Possibly not needed since the settings are already discussed in iosettings

Export
======
.. _workflow-export:

***********Make mesh -> Object panel -> Shader -> geometry -> armature (?) -> material properties -> textures -> collision

Now we'll deal with all the steps needed to export your .nif file.

#. Create your base model;
#. Configure nif versions and general flags;
#. Configure shaders;
#. Revise your object geometry;
#. Cofigure your bones [optional - only if you have an armature];
#. Configure your materials;
#. Configure your textures;
#. Create your model's collision;
#. Export with the correct settings.

Step 1: Base Model
^^^^^^^^^^^^^^^^^^
.. _workflow-basemesh:

Create/Modify your intended model in blender. If you need an introduction to blender consider reading `this e-book <https://en.wikibooks.org/wiki/Blender_3D:_Noob_to_Pro>`_.

Step 2: General Nif Info
^^^^^^^^^^^^^^^^^^^^^^^^
.. _workflow-geninfo:

Add in the general info required to identify the .nif file, refer to

***********Create new section for this

Step 3: Shaders
^^^^^^^^^^^^^^^
.. _workflow-shader:

Configure the shaders for each selected object, refer to

***********Create new section for this

Step 4: Revising Geometry
^^^^^^^^^^^^^^^^^^^^^^^^^
.. _workflow-geom:

Configure the shaders for each selected object, refer to the :ref:`Geometry Section <geometry-mesh>`.

Step 5: Bone Flags
^^^^^^^^^^^^^^^^^^
.. _workflow-boneflag:

Configure the flags for each selected bone, refer to the :ref:`Armature Section <armature-armatures>`. If you don't have an armature you can skip this step.

Step 6: Materials
^^^^^^^^^^^^^^^^^
.. _workflow-materials:

Configure the materials for each selected object, refer to the :ref:`Materials Section <properties-material>`.

Step 7: Texture Types
^^^^^^^^^^^^^^^^^^^^^
.. _workflow-textures:

Configure the textures for each selected object, refer to the :ref:`Textures Section <texture_maps>`.

Step 8: Adding Collision
^^^^^^^^^^^^^^^^^^^^^^^^
.. _workflow-collision:

Add in collision for each selected object, refer to the :ref:`Collision Section <collision-workflow>`.

Step 9: Exporting
^^^^^^^^^^^^^^^^^
.. _workflow-exportexport:

You're now ready to export! These settings are explained at :ref:`I/O Settings Section <iosettings>`.
 



