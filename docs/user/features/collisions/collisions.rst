
Bounding Box
============

This is used as the bound box.

#. Create a Mesh-Object to represent the bound box, a Cube is recommended.

#. Name the object BSBound or BoundingBox, depending on which version you wish to be exported.

#. In the Object Tab, enable bounds in the display section.

Collision
=========
.. _collision:

This is used by the havok system for collision detection.

.. warning::

   * Collisions are in the process of being ported. This section is subject to change.
   * For Cylender Export, we need to fix them to show how the user would create the objects. We are using a Meta Capsule
   * Some of the collision types lack viewport rendering, see workaround for visulisations below.

Notes
~~~~~
.. _collision-notes:

* Collision Bounds are represented by a dashed line, unlike Bounds which are by solid lines. 

Collision Mapping
~~~~~~~~~~~~~~~~~
.. _collision-mapping:

* The following section describes the most appropriate primitive object to represent the desired collision object type.
* The suggested shapes also correspond to how the shapes will look as imported by the scripts.
* On export the BhkShape is created from data pulled from the Collision object.

Blender's Collision types map to the following Nif types:

- Oblivion, Fallout 3, and Fallout NV; 

+----------------------------+------------------------+
| Blender                    | Nif                    |
+============================+========================+
| `Box Collision`_           | bhkBoxShape            |
+----------------------------+------------------------+
| `Sphere Collision`_        | bhkSphereShape         |
+----------------------------+------------------------+
| `Capsule Collision`_       | bhkCapsuleShape        |
+----------------------------+------------------------+
| `Convex Hull Collision`_   | bhkConvexVerticesShape |
+----------------------------+------------------------+
| `Triangle Mesh Collision`_ | bhkMoppBvTreeShape     |
+----------------------------+------------------------+

- Morrowind:

+----------------------------+-------------------+ 
| Blender                    | Nif               |
+============================+===================+
| `Triangle Mesh Collision`_ | RootCollisionNode |
+----------------------------+-------------------+

Box Collision
~~~~~~~~~~~~~
.. _collison-box:

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create a second mesh-object to represent our collision object, a primitive cube(prim-cube) is recommended.

#. Rename the prim-cube via the Object panel, eg. 'CollisionBox'

#. Scale the 'CollisionBox' uniformly to the size wanted.

#. :ref:`Add physics to our 'CollisionBox' <collison-settings>`.

Sphere Collision
~~~~~~~~~~~~~~~~
.. _collision-sphere:

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create another mesh-object to represent our collision shape, a primitive sphere(prim-sphere) is highly recommended.

#. Rename the prim-sphere via the Object panel, eg. 'CollisionSphere' 

#. Scale the 'CollisionSphere' object as needed, ensuring all vertices are enclosed by the sphere

#. :ref:`Add physics to our 'CollisionSphere' <collison-settings>`.

Capsule Collision
~~~~~~~~~~~~~~~~~
.. _collision-capsule:

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create a second mesh-object to represent our collision object, a primitive cylinder(prim-cylinder) is recommended.

#. Select the second newly created prim-cylinder, rename it appropriately, eg. 'CollisionCapsule' via the Object panel.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our 'CollisionCapsule' <collison-settings>`.

Capsule Notes
+++++++++++++
.. _collision-capsule-notes:

* If the lenght is less than or equal to the radius, then a :class:`~pyffi.formats.nif.NifFormat.bhkSphereShape` is generated instead.
* Currently Capsule bounds lack viewport preview, awaiting Bullet Physic integration
* The following is a workaround; **Prone to user error, Ensure to reset setting after visualising!**.
#.   In the **Object Tab**, under the **Display** section enable **Bounds**
#.   Set the **Type** to **Cylinder**.
 
 This shape best represents the capsule, but is missing the end caps which are hemi-spheres. 

Convex Hull Collision
~~~~~~~~~~~~~~~~~~~~~
.. _collision-convex-hull:

#. :ref:`Create your mesh-object <geometry-mesh>`. 

#. Create a convex mesh. See :ref:`Notes <collision-convex-hull-notes>`

#. Select the newly created mesh-object and rename it, eg. 'CollisionHull' via the Object panel.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Convex Hull Notes
+++++++++++++++++
.. _collision-convex-hull-notes:

* It is advisable to use a convex hull generator to create the collision-mesh.

Triangle Mesh Collision
~~~~~~~~~~~~~~~~~~~~~~~
.. _collision-triangle-mesh:

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create a convex hulled mesh-object. See :ref:`Notes<collision-convex-hull-notes>`

#. Select the newly mesh and rename it, eg. 'CollisionPolyhedron' via the Object panel.

#. Scale the collision cube 'CollisionPoly' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

Triangle Mesh Notes
+++++++++++++++++++
.. _collision-triangle-mesh-notes:

* Often a duplicate object can be used, simplified by decimating, then triangulated(**Ctrl + T**).
* A :ref:`Convex Hulled Object<collision-convex-hull-notes>` can also be used.

Collision Settings
~~~~~~~~~~~~~~~~~~
.. _collison-settings:

* Meshes with Collision Bounds enabled will be exported as a :class:`~pyffi.formats.nif.NifFormat.bhkShape`, rather than a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* The Collision settings are used by the :class:`~pyffi.formats.nif.NifFormat.bhkShape` to control it reacts in the Havok physics simulation.

Example
~~~~~~~

First we enable Collision Setting for the selected Collision Object:

#. In the the **Physics** tab, enable **Collision Bounds** 

The bounds type is used to select which BhkShape type to use.

#. Enable the desired **Bounds** type.

The Havok Material decides how the material should behave for collisions, eg. sound, decals.

#. Select a Havok Material from the list.

.. todo::

   write up layer, quality type, motion system, etc.



