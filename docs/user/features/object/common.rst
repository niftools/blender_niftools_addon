

Nif Version
-----------
.. _object-common-version:

* Nif Version
   The base version, generally related to a single game or company. Displayed in format xx.xx.xx.xx
   
**Example:**

   Nif Version 20.02.00.07 is the version that is used for Fallout 3

* User Version
   A two digit single integer sub value of Nif Version
   11 Would designate Fallout 3 as the specific game file.
   
* User Version 2:
   A second two digit single integer sub value, with the same function as User Version.

**Notes:**

   * All three values are used to verify which data should be attached to a file during the export process.
   * The values of each object are checked against the root object during export, any
      mismatches will trigger and error and alert the user so that corrections can be effected.

      
BSX
---
.. _object-common-bsx:

BSX is a flagging variable that determines how havok will interact with the object
   * Havok = 1
   * Collision = 2
   * Is armature (?) = 4
   * Enable animation = 8
   * Flame nodes = 16
   * Editor marker present = 32

**Notes:**
   The value is equal to the sum of all items that are enabled.
   to enable havok and collision the value would be 3
   
   
BS Inventory Marker
-------------------
.. _object-mesh-bsinvmarker:

* BS Inv Marker
   This sets the x, y, z rotation and zoom level of objects for the in game inventory display in games that support the property.
   
#. With blender in Object mode, open the BS Inv Marker property window and click + 
   This should only be applied to the Root object, For rigged meshed this should be applied to the armature, For non rigged objects it should be applied to the Mesh object
#. Apply desired values to x,y,z to set the preferred rotation.
   #. Set view to back view and use rotation to achieve the preferred object orientation.
   #. Copy the values from the rotation display into the x,y,z lines for BS Inv Marker.
   #. Delete the decimal and remove any numbers to the right of the fourth digit.
   #. Press alt + R to reset the object rotation back to 0
#. Apply desired value to zoom   
   #. a value of 1 for zoom is the default, lower values .99 to .01 decrease the item size in the menu.
      
   
**Notes:**
* Rigged objects that use this value may also use :ref:`InvMarker Bones <armature-invmarker>`.


UPB
---
.. _object-mesh-upb:

The UPB is a group of values contained in a single data string. It's use is unknown. 
   * Niftools uses Mass = 0.000000\r\nEllasticity = 0.300000\r\nFriction = 0.300000\r\nUnyielding = 0\r\nSimulation_Geometry = 2\r\nProxy_Geometry = <None>\r\nUse_Display_Proxy = 0\r\nDisplay_Children = 1\r\nDisable_Collisions = 0\r\nInactive = 0\r\nDisplay_Proxy = <None>\r\n as the default value set for this item.

      