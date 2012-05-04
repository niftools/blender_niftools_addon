
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
   * We will eventually move the Physics collision panel from BGE to Blender Render.
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