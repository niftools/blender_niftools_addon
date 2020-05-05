Object Settings
===============
.. _user-feature-object:

This section will take you through the base settings required for your model.

.. add something more here
.. May break up the common by type; armature, mesh, common etc?


BSX
---
.. _user-feature-object-bsx:

**BSX** is a flagging variable that determines how havok will interact with the object:

   * Havok = 1
   * Collision = 2
   * Is armature (?) = 4
   * Enable animation = 8
   * Flame nodes = 16
   * Editor marker present = 32

   *Example:*
      To enable havok and collision the value would be 3.


.. note::
   * The value is equal to the sum of all items that are enabled.
   
   
.. _user-feature-object-mesh-bsinvmarker:

BS Inventory Marker
-------------------

**BS Inv Marker**
   This sets the x, y, z rotation and zoom level of objects for the in-game inventory display in games that support the property.
   
#. With Blender in Object mode, open the BS Inv Marker property window and click "*+*".
   
.. note::
   * This should only be applied to the Root object:
      * For rigged meshed this should be applied to the armature, for non-rigged objects it should be applied to the Mesh object.

2. Apply desired values to x,y,z to set the preferred rotation.

   a. Set view to back view and use rotation to achieve the preferred object orientation.
   #. Copy the values from the rotation display into the x,y,z lines for BS Inv Marker.
   #. Delete the decimal and remove any numbers to the right of the fourth digit.
   #. Press Alt + R to reset the object rotation back to 0
   
#. Apply desired value to zoom   

   a. A value of 1 for zoom is the default, lower values .99 to .01 decrease the item size in the menu.
      
   
.. note::
   * Rigged objects that use this value may also use :ref:`InvMarker Bones <armature-invmarker>`.


.. _object-mesh-upb:

UPB
---

The **UPB** is a group of values contained in a single data string. Its use is unknown. 

Niftools uses the following values as default for this item.:

   * Mass = 0.000000
   * Elasticity = 0.300000
   * Friction = 0.300000
   * Unyielding = 0
   * Simulation_Geometry = 2
   * Proxy_Geometry = <None>
   * Use_Display_Proxy = 0
   * Display_Children = 1
   * Disable_Collisions = 0
   * Inactive = 0
   * Display_Proxy = <None>


Settings
--------
.. _user-feature-object-settings:

First, we complete the object panel:

   #. The **Nif Root Node** determines the kind of block used at the nif's root. Select one from the drop-down box.
   #. The **BS Num UV Set** is ????????. Set it to an appropriate number.
   #. The **UPB**'s use is currently unknown. It is recommended you leave it at the default value.
   #. Set your **BSX Flags**.
   #. The **Consistency Flag** is ????????. Select one from the drop-down box.
   #. The **Object Flag** is ???????. Set it to an appropriate number.
   #. The **Nif Long Name** is ???????. Set it to an appropriate string.   

.. Extra Data and InvMarkers I have no idea how to fill them in. Help?


Node Types
---

Blender empties can represent various NIF node types, and are selected according to the following criteria:

   * In the 'Object Constraints Panel', add a 'Track To' object constraint to create a 'NiBillboardNode' that always faces the camera.
   * Add a custom property to create a 'NiLODNode'. Set Near extent and far extent as properties on the Lod controller's children.
   * Select the root node type from the dropdown menu.

   
   