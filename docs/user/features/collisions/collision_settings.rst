
.. _collisonsettings:

Collision Settings
------------------

The following section details the setting which need to be applied to the collision body to react appropriately in the collision simulation.
A lot of these setting are havok specific; where possible we have mapped them to blender's collision simulation.


.. _collisonsettings-enable:

Enabling Collisions
===================

First we enable Collision Setting for the selected Collision Object:

* In the the **Physics** tab, enable **Collision Bounds** 

* Meshes with Collision Bounds enabled will be exported as a :class:`~pyffi.formats.nif.NifFormat.bhkShape`, rather than a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.


The bounds type is used to select which BhkShape type to use.

* Select the desired **Bounds** type from the dropdown box.


.. _collisonsettings-havok:

Havok Settings
==============

* The Collision settings are used by the :class:`~pyffi.formats.nif.NifFormat.bhkShape` to control it reacts in the Havok physics simulation.

.. 
   todo::

   Probably a better way to display the information too, perhaps a table with setting -> detail?. Could bloat though.
   Decide if we should reference the nif.xml directly or improve tooltips?


   The **Radius** is used as region around the collision object.
   If another collision object intersects this region; a quickier, but less accurate collision algorithm is used. 
   If the object intersects futher than the region value, then full collision calculation occurs.
   
   * Set the **Radius** to the appropriate number.
   
   The **Havok Material** decides how the material should behave for collisions, eg. sound, decals.
   
   * Select a **Havok Material** from the dropdown box.
   
                     Velocity Max does not seem to be used in the nif.
   
   The **Collision Filter Flags** determines
   
   * Set the **Col Filter** to the appropriate number.
   
   The **Deactivator Type** determines .
   
   * Select a **Deactivator Type** from the dropdown box.
   
   The **Solver Deactivator** determines .
   
   * Select a **Solver Deactivator** from the dropdown box.
   
   The **Quality Type** determines .
   
   * Select a **Quality Type** from the dropdown box.
   
   The **Oblivion Layer** determines.
   
   * Select a **Oblivion Layer** from the dropdown box.
   
   The **Max Linear Velocity** determines .
   
   * Set the **Max Linear Velocity** to the appropriate number.
   
   The **Max Angular Velocity** determines .
   
   * Set the **Max Angular Velocity** to the appropriate number.
   
   The **Motion System** determines .
   
   * Select a **Motion System** from the dropdown box.
   
   The **LHMaxFriction** determines .
   
   * Set the **LHMaxFriction** to the appropriate number.
   
   The **tau** determines .
   
   * Set the **tau** to the appropriate number.
   
   The **Damping** determines .
   
   * Set the **Damping** to the appropriate number.

