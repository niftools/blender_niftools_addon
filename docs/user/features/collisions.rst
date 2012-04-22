
Collision
---------

.. warning::

   Collisions are in the process of being ported. This section is incomplete and will change.

Example
~~~~~~~

.. _features-example-collisions:

#. To indicate the physics properties for an object, switch to the **Blender Game** tab. (Default tab is **Blender Render**)
#. With the collision object selected, switch to the **Physics** tab
#. Click **Collision Bounds** and select **Box** as **Bounds**
#. If you would like to define your own settings for havok physics, click **Use Blender Properties**.    
#. Define the fields **Havok Material**, **Motion System**, **Oblivion Layer**, **Quality Type** and **Col Filter** accordingly.
#. If you want the exporter to define the havok physics properties for you, make sure **Use Blender Properties** is not clicked.
#. Now you can continue editing the mesh until you are ready to export. 

.. todo::
   Should "Use Blender Properties" usage be reversed?
   i.e "Use Blender Property" uses default values, else define your own. Also should that there are defined by user else user default.

Notes
~~~~~

We need to indicate that a mesh is to be exported as a collision object, rather than a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`,

* Select the blender **Game Engine** renderer, 
* Select the object's physics tab, enable the **Collision Bounds** option, 
* Select the desired **Bounds**. 


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
| `Triangle Mesh Collision`_ | bhkMoppByTreeShape     |
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
.. _example-box-collison:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <example-box-collison>`.

Box Collision Notes
+++++++++++++++++++

Test

Sphere Collision
~~~~~~~~~~~~~~~~

.. _example-sphere-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <example-box-collison>`.

Sphere Collision Notes
++++++++++++++++++++++

Cylinder Collision
~~~~~~~~~~~~~~~~~~

.. _example-cylinder-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <example-box-collison>`.

Cylinder Collision Notes
++++++++++++++++++++++++

Capsule Collision
~~~~~~~~~~~~~~~~~

.. _example-capsule-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <example-box-collison>`.

Capsule Collision Notes
+++++++++++++++++++++++

Currently there is no visualisation in Blender for Capsule Collisions.

Convex Hull Collision
~~~~~~~~~~~~~~~~~~~~~

.. _example-convex-hull-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <example-box-collison>`.

Convex Hull Collision Notes
+++++++++++++++++++++++++++

Triangle Mesh Collision
~~~~~~~~~~~~~~~~~~~~~~~

.. _example-triangle-mesh-collision:

#. :ref:`Create a single sided cube <features-example-geometry>`
   as explained before.

#. :ref:`Create another single sided cube <features-example-geometry>`
   as explained before.

#. Select the second newly created cube and rename it, like 'CollisionBox' via the Object panel

#. In the Object panel, under Display, select Type and change it to **Wire**, this will make it easier to find.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <example-box-collison>`.

Triangle Mesh Collision Notes
+++++++++++++++++++++++++++++

Bounding Box
------------

.. todo::

   Write.
