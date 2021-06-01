.. _user-features-iosettings-export:
Export Settings
===============

This section explains the import and export settings.

.. warning::
   Only a subset of these settings is currently supported even though they have been documented.
   This is due to the fact that they are ported directly from the old addon and as such, will functionally remain the
   same.

.. _user-features-iosettings-export-scale:
Scale correction
----------------

This value is used to globally re-scale the Blender system of measurement units to the Nif Format units.

* The ratio of a Nif Units (NU) to Blender Units (BU) is 1Bu:0.1Nu. or each NU is about 10x larger than a BU.
* The Blender Niftools Addon applies a default correction of 10
* The default setting ensures the imported model fits into the view Blender viewport.

.. _user-features-iosettings-export-armature:
Armature
--------

.. _user-features-iosettings-export-flattenskin:
Flatten Skin
^^^^^^^^^^^^

This option should remove the hierarchy of the bones in the exported nif. However, it is currently not used in export.
In order to flatten the hierarchy before export with Blender: Select the bones in object mode, then go into edit mode
and use ``Alt+P`` to unparent the bones with the``Clear Parent`` option.

.. _iosettings-padnsort:
Pad & Sort Bones
^^^^^^^^^^^^^^^^

Adjusts the number of bones in a given partition to match the total number of bones used for the dismember instance.

.. _iosettings-maxpartitionbones:
Max Partition Bones
^^^^^^^^^^^^^^^^^^^

The maximum number of bones that a single dismember partition can use before starting a new partition.

.. _iosettings-maxvertexbones:
Max Vertex Bones
^^^^^^^^^^^^^^^^

The maximum number of bone weight values that can be applied to a single vertex.

.. _user-features-iosettings-export-game:
Game
----

A list of supported games which the addon will export working nif files.

.. _user-features-iosettings-export-animation:
Animation
-------

Determines how to export the data in the blend file.

Export options include
* All (nif) - Geometry and animation to a single nif.
* All (nif, xnif, xkf) - Geometry and animation to a nif. Generates an xnif, and xkf.
* Geometry only (nif) - Only geometry to a single nif.
* Animation only (kf) - Only animation to a single kf.

.. _iosettings-bsanimationnode:
Use NiBSAnimationNode
^^^^^^^^^^^^^^^^^^^^^

NiBSAnimationNode is specific to "The Elder Scrolls - Morrowind" and should only be used when exporting animated
items for that game.

.. _user-features-io_settings-export-optimise:
Optimise
--------

.. _user-features-io_settings-export-stripifygeometries:
Stripify Geometries
^^^^^^^^^^^^^^^^^^^

Export with NiTriStrips instead of NiTriShapes.

.. _user-features-iosettings-export-stitchstrips:
Stitch Strips
^^^^^^^^^^^^^

Whether to stitch NiTriStrips (if they are used). Important for Civilization IV.

.. _user-features-iosettings-export-forcedds:
Force DDS
^^^^^^^^^

Changes the suffix for the texture file path in the nif to use .dds

.. _user-features-io_settings-export-optimisematerials:
Optimise Materials
^^^^^^^^^^^^^^^^^^

Remove duplicate materials. Currently not used.