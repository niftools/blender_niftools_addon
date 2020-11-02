Export Settings
===============
.. _user-features-iosettings-export:

This section explains the import and export settings.

.. warning::
   Only a subset of these settings is currently supported even though they have been documented. 
   This is due to the fact that they are ported directly from the old plugin and as such, will functionally remain the same.


Scale correction
----------------
.. _user-features-iosettings-export-scale:

This value is used to globally re-scale the Blender system of measurement units to the Nif Format units.

* The ratio of a Nif Units (NU) to Blender Units (BU) is 1Bu:0.1Nu. or each NU is about 10x larger than a BU.
* The Blender Niftools Addon applies a default correction of 10
* The default setting ensures the imported model fits into the view Blender viewport.


Game
----
.. _user-features-iosettings-export-game:

A list of supported games which the plugin will export working nif files.


Process
-------
.. _user-features-iosettings-export-process:

Determines how to export the data in the blend file.

Export options include
* All (nif) - Geometry and animation to a single nif.
* All (nif, xnif, xkf) - Geometry and animation to a nif. Generates an xnif, and xkf.
* Geometry only (nif) - Only geometry to a single nif.
* Animation only (kf) - Only animation to a single kf.


Smooth Inter-Object Seams
-------------------------
.. _user-features-iosettings-export-smoothseams:

This option combines the normals data for all vertices containing the same XYZ location data along an edge and uses the same normal tangent and bi-tangent values for all affected vertices.

Use NiBSAnimationNode
---------------------
.. _iosettings-bsanimationnode:

NiBSAnimationNode is specific to "The Elder Scrolls - Morrowind" and should only be used when exporting animated items for that game.

Flatten Skin
------------
.. _user-features-iosettings-export-flattenskin:

This option does something to the thing, no really it does, but I can't tell you because it's a sekret.

Pad & Sort Bones
----------------
.. _iosettings-padnsort:

Adjusts the number of bones in a given partition to match the total number of bones used for the dismember instance.

Max Partition Bones
-------------------
.. _iosettings-maxpartitionbones:

The maximum number of bones that a single dismember partition can use before starting a new partition.

Max Vertex Bones
----------------
.. _iosettings-maxvertexbones:

The maximum number of bone weight values that can be applied to a single vertex.

Force DDS
---------
.. _user-features-iosettings-export-forcedds:

Changes the suffix for the texture file path in the nif to use .dds

