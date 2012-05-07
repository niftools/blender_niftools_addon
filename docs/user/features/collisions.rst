
Bounding Box
============

.. warning::
   Currently unsupported

Collision
=========
.. _collisions:

This is used by the havok system for collision detection

.. warning::

   * Collisions are in the process of being ported. This section is incomplete and will change.
   * The Collision Bounds panel is located in the Physics tab of Blender Render and Blender Game.
   * Some of the collision types lack viewport rendering, see workaround for visulisations below.

For Oblivion, Fallout 3, and Fallout NV; Blender's Collision types map to the following Nif types:

+----------------------------+------------------------+
| Blender                    | Nif                    |
+============================+========================+
| `Box Collision`_           | bhkBoxShape            |
+----------------------------+------------------------+
| `Sphere Collision`_        | bhkSphereShape         |
+----------------------------+------------------------+
| `Cylinder Collision`_      | bhkCylinderShape       |
+----------------------------+------------------------+
| `Capsule Collision`_       | bhkCapsuleShape        |
+----------------------------+------------------------+
| `Convex Hull Collision`_   | bhkConvexVerticesShape |
+----------------------------+------------------------+
| `Triangle Mesh Collision`_ | bhkMoppBvTreeShape     |
+----------------------------+------------------------+

For Morrowind, we have:

+----------------------------+-------------------+ 
| Blender                    | Nif               |
+============================+===================+
| `Triangle Mesh Collision`_ | RootCollisionNode |
+----------------------------+-------------------+

.. todo::

   Where do we store material, layer, quality type, motion system, etc.?
   Are the tables bellow ok?
   
For Havok Materials, we have:

+----------------------------+------------------------------+
| Material name              | Havok Material Name          |
+============================+==============================+
| Stone                      | HAV_MAT_STONE                |
+----------------------------+------------------------------+
| Cloth                      | HAV_MAT_CLOTH                |
+----------------------------+------------------------------+
| Dirt                       | HAV_MAT_DIRT                 |
+----------------------------+------------------------------+
| Glass                      | HAV_MAT_GLASS                |
+----------------------------+------------------------------+
| Grass                      | HAV_MAT_GRASS                |
+----------------------------+------------------------------+
| Metal                      | HAV_MAT_METAL	            |
+----------------------------+------------------------------+
| Organic                    | HAV_MAT_ORGANIC	            |
+----------------------------+------------------------------+
| Metal                      | HAV_MAT_METAL	            |
+----------------------------+------------------------------+
| Skin                       | HAV_MAT_SKIN 	            |
+----------------------------+------------------------------+
| Water                      | HAV_MAT_WATER	            |
+----------------------------+------------------------------+
| Wood                       | HAV_MAT_WOOD                 |
+----------------------------+------------------------------+
| Heavy Stone                | HAV_MAT_HEAVY_STONE          |
+----------------------------+------------------------------+
| Heavy Metal                | HAV_MAT_HEAVY_METAL          |
+----------------------------+------------------------------+
| Heavy Wood                 | HAV_MAT_HEAVY_WOOD           |
+----------------------------+------------------------------+
| Chain                      | HAV_MAT_CHAIN	            |
+----------------------------+------------------------------+
| Snow                       | HAV_MAT_SNOW                 |
+----------------------------+------------------------------+
| Stone Stairs               | HAV_MAT_STONE_STAIRS         |
+----------------------------+------------------------------+
| Cloth Stairs               | HAV_MAT_CLOTH_STAIRS         |
+----------------------------+------------------------------+
| Dirt Stairs                | HAV_MAT_DIRT_STAIRS          |
+----------------------------+------------------------------+
| Glass Stairs               | HAV_MAT_GLASS_STAIRS         |
+----------------------------+------------------------------+
| Grass Stairs               | HAV_MAT_GRASS_STAIRS         |
+----------------------------+------------------------------+
| Metal Stairs               | HAV_MAT_METAL_STAIRS         |
+----------------------------+------------------------------+
| Organic Stairs             | HAV_MAT_ORGANIC_STAIRS       |
+----------------------------+------------------------------+
| Skin Stairs                | HAV_MAT_SKIN_STAIRS          |
+----------------------------+------------------------------+
| Water Stairs               | HAV_MAT_WATER_STAIRS         |
+----------------------------+------------------------------+
| Heavy Stone Stairs         | HAV_MAT_HEAVY_STONE_STAIRS   |
+----------------------------+------------------------------+
| Heavy Metal Stairs         | HAV_MAT_HEAVY_METAL_STAIRS   |
+----------------------------+------------------------------+
| Heavy Wood Stairs          | HAV_MAT_HEAVY_WOOD_STAIRS    |
+----------------------------+------------------------------+
| Chain Stairs               | HAV_MAT_CHAIN_STAIRS         |
+----------------------------+------------------------------+
| Snow Stairs                | HAV_MAT_SNOW_STAIRS          |
+----------------------------+------------------------------+
| Elevator                   | HAV_MAT_ELEVATOR             |
+----------------------------+------------------------------+
| Rubber                     | HAV_MAT_RUBBER               |
+----------------------------+------------------------------+

For Havok Motion System we have:

+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Havok Motion System Name     | Description                                                                                                                                                            |
+==============================+========================================================================================================================================================================+
| MO_SYS_INVALID               | Invalid                                                                                                                                                                |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_DYNAMIC               | A fully-simulated, movable rigid body. At construction time the engine checks the input inertia and selects MO_SYS_SPHERE_INERTIA or MO_SYS_BOX_INERTIA as appropriate.|
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_SPHERE                | Simulation is performed using a sphere inertia tensor.                                                                                                                 |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_SPHERE_INERTIA        | This is the same as MO_SYS_SPHERE_INERTIA, except that simulation of the rigid body is "softened".                                                                     |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_BOX                   | Simulation is performed using a box inertia tensor.                                                                                                                    |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_BOX_STABILIZED        | This is the same as MO_SYS_BOX_INERTIA, except that simulation of the rigid body is "softened".                                                                        |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_KEYFRAMED             | Simulation is not performed as a normal rigid body. The keyframed rigid body has an infinite mass when viewed by the rest of the system. (used for creatures)          |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_FIXED                 | This motion type is used for the static elements of a game scene, e.g. the landscape. Faster than MO_SYS_KEYFRAMED at velocity 0. (used for weapons)                   |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_THIN_BOX              | A box inertia motion which is optimized for thin boxes and has less stability problems.                                                                                |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MO_SYS_CHARACTER             | A specialized motion used for character controllers.                                                                                                                   |
+------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Box Collision
~~~~~~~~~~~~~
.. _collison-box:

#. :ref:`Create your mesh-object <geometry-mesh>` as explained before.

#. Create another mesh-object to represent our collision shape, a primitive cube(prim-cube) is highly recommended.

#. Rename the prim-cube via the Object panel, eg. 'CollisionBox'

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Box Notes
+++++++++

Test

Sphere Collision
~~~~~~~~~~~~~~~~

.. _collision-sphere:

#. :ref:`Create a mesh geometry <geometry-mesh>`
   as explained before.

#. Create another mesh-object to represent our collision shape, a primitive sphere(prim-sphere) is highly recommended.

#. Rename it to something more appropriate, like 'CollisionSphere' via the Object panel

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Sphere Notes
++++++++++++

Cylinder Collision
~~~~~~~~~~~~~~~~~~

.. _collision-cylinder:

#. :ref:`Create a single sided cube <geometry-mesh>`
   as explained before.

#. :ref:`Create another single sided cube <geometry-mesh>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Cylinder Notes
++++++++++++++

Capsule Collision
~~~~~~~~~~~~~~~~~

.. _collision-capsule:

#. :ref:`Create a single sided cube <geometry-mesh>`
   as explained before.

#. :ref:`Create another single sided cube <geometry-mesh>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Capsule Notes
+++++++++++++

Currently there is no visualisation in Blender for Capsule Collisions.

Convex Hull Collision
~~~~~~~~~~~~~~~~~~~~~

.. _collision-convex-hull:

#. :ref:`Create a single sided cube <geometry-mesh>`
   as explained before.

#. :ref:`Create another single sided cube <geometry-mesh>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Convex Hull Notes
+++++++++++++++++

Triangle Mesh Collision
~~~~~~~~~~~~~~~~~~~~~~~

.. _collision-triangle-mesh:

#. :ref:`Create a single sided cube <geometry-mesh>`
   as explained before.

#. Create another mesh-object to represent our collision shape, a primitive sphere(prim-sphere) is highly recommended.

#. Select the newly created second polyheadron and rename it something collision related, like 'CollisionPoly' via the Object panel.

#. Scale the collision cube 'CollisionPoly' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Triangle Mesh Notes
+++++++++++++++++++

Collision Settings
~~~~~~~~~~~~~~~~~~
.. _collison-settings:

* The Collision settings are used by the :class:`~pyffi.formats.nif.NifFormat.bhkShape` to control how the collision shape reacts in the Havok physics simulation.

Example
~~~~~~~

#. Switch to the **Blender Game** tab. (Default tab is **Blender Render**)
#. Select the collision object in the viewport
#. In the the **Physics** tab, enable **Collision Bounds** 
#. Enable the desired **Bounds** type, see below for more details 

.. todo::
   Should "Use Blender Properties" usage be reversed? i.e "Use Blender Property" uses default values
   This should be enabled by default, else define your own. 
   Should there be an additional check to see if not selected, that user has actually defined their own?
   
#. If you would like to define your own settings for havok physics, click **Use Blender Properties**.    
#. Define the fields **Havok Material**, **Motion System**, **Oblivion Layer**, **Quality Type** and **Col Filter** accordingly.
#. If you want the exporter to define the havok physics properties for you, make sure **Use Blender Properties** is not clicked.

Notes
~~~~~

* Enable the **Collision Bounds** option, the mesh will be exported as a :class:`~pyffi.formats.nif.NifFormat.bhkShape, rather than a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`,
* Collision Bounds are represented by a dashed line, unlink Bounds which is a solid line. 
* Currently Capsule, Convex Hull and Triangle Mesh lack viewport preview.
   - In **Render** tab, under the **Display** section enable **Physics Visualisation**
   - **Game -> Start Game Engine** (p-key).
   - Set the **Viewport Shading** to **Wireframe or Bounding Box**.
   - Collisions Bounds will be displayed by a green wireframe