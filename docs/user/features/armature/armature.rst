Armature Bones
--------------
.. _armature-armatures:

* The following section deals with Armatures




Inventory Marker
----------------
.. _armature-invmarker:

* This Is a special type of bone which is used to position object in the inventory display.
	It may also be used for animation placement involving multiple NPCs
* The InvMarker bone should only be used in engines that can support them.
**Example:**
	
#. Create this item in the same manner as you would for a standard armature bone.
#. parent must be Armature root
#. Naming must start with InvMarker and can only be appended with .000
	A model with 4 inventory marker bone items should be named as InvMarker, InvMarker.001, InvMarker.002, InvMarker.003 
	
**Notes:**
*	Games known to support this include
		The Elder Scrolls - Skyrim
*	Exporting this type of bone into engines that do not support it will cause crashes.