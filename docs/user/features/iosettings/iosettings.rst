Import and Export Settings
--------------------------
.. _iosettings:

This section explains the import and export settings.

.. warning::
   Only a subset of these settings are currently supported even though they have been documented. 
   This is due to the fact that they are ported directly from the old plugin and as such, will functionally remain the same.

Align
-----
.. _iosettings-align:

Align selects how to align the tail position of non parented bones to the root location.

* Options are
	* Re-Align Tail Bone - Aligns the tail of non parented bones to a uniform direction.
	* Re-Align Tail Bone + roll - Sets a 90 degree roll to the tail after aligning. 

Scale correction
----------------
.. _iosettings-scale:

* Scale Correction Import
	The relative scale of Nif units to blender unit is 10:1.
   The Blender Nif Plugin applies a default correction of 0.1 so that the imported model will fit into the view Blender viewport.
   When importing large-scale nif models, such as structures, the user can edit this value.

* Scale Correction Export
	Reverses the scale applied during import. nif scripts default value is 10.

Log Level
---------
.. _iosettings-loglevel:

* Log Level
	The level at which a log entry is generated. This is used for debugging and error checking. The user will rarely have a need to alter this setting.
	
Keyframe File
-------------
.. _iosettings-keyframe:

* keyframe file ( .kf ) is an animation file using key frame markers
* A more complex animation file introduced with Skyrim ( .hkx ) is basically a compressed file containing .kf files.


EGM File
--------
.. _iosettings-egm:

* EGM files are a vertex morph animation file, most commonly used for facial animations and lip synch.

Animation
---------
.. _iosettings-animation:

* Animation option, when selected, will import the :ref:`keyframe <iosettings-keyframe>` and/or the :ref:`EGM <iosettings-egm>` files listed in the file selection entries.



Combine Shapes
--------------
.. _iosettings-combineshapes:

Select this option if you want all parts of a nif file to be imported as a single multi-part object. 
This is useful for keeping nifs organized when they contain several parts. As well as allowing for easier exporting of the nif.

Combine Vertices
----------------
.. _iosettings-combinevertex:

This options will combine vertices that contain the same x,y,z location and normal data into a single vertex.
Select this when vertex ordering is not critical, non animated objects or animated objects that use a skeleton for the animations, but do not contain morph animations.
Do not use this for any object that uses morph type animations.

Flatten Skin
------------
.. _iosettings-flattenskin:

This option does something to the thing, no really it does, but I can't tell you because it's a sekret.

Force DDS
---------
.. _iosettings-forcedds:

Changes the suffix for the texture file path in the nif to use .dds

Game
----
.. _iosettings-game:

A list of supported game for which the nif plugin will export working files.

Max Partition Bones
-------------------
.. _iosettings-maxpartitionbones:

The maximum number of bones that a single dismember partition can use before starting a new partition.

Max Vertex Bones
----------------
.. _iosettings-maxvertexbones:

The maximum number of bone weight values that can be applied to a single vertex.

Pad & Sort Bones
----------------
.. _iosettings-padnsort:

Adjusts the number of bones in a given partition to match the total number of bones used for the dismember instance.

Process
-------
.. _iosettings-process:

Determines what parts of the file to import.

* Import options include
	* Everything - This will import geometry, armature, (keyframe, and EGM if set).
	* Geometry only - Imports geometry and skips all other parts of the file.
	* Skeleton only - Imports the armature and skips all other parts of the file.

* Export options include
	* All (nif) - Geometry and animation to a single nif.
	* All (nif, xnif, xkf) - Geometry and animation to a nif. Generates an xnif, and xkf.
	* Geometry only (nif) - Only geometry to a single nif.
	* Animation only (kf) - Only animation to a single kf.
	
Smooth Inter-Object Seams
-------------------------
.. _iosettings-smoothseams:

This option combines the normals data for all vertices containing the same xyz location data along an edge and uses the same normal tangent and bi-tangent values for all affected vertices.

Use NiBSAnimationNode
---------------------
.. _iosettings-bsanimationnode:

NiBSAnimationNode is specific to "The Elder Scrolls - Morrowind" and should only be used when exporting animated items for that game.

