
Bounding Box
============

This is used as the bound box.

#. Create a Mesh-Object to represent the bound box, a Cube is recommended.

#. Name the object BSBound or BoundingBox, depending on which version you wish to be exported.

#. In the Object Tab, enable bounds in the display section.



*************Which games use this?

Collision
=========
.. _collision:

This is used by the havok system for collision detection.

.. warning::

   * Collisions are in the process of being ported. This section is subject to change.
   * For Cylinder Export, we need to fix them to show how the user would create the objects. We are using a Meta Capsule
   * Some of the collision types lack viewport rendering, see workaround for visulisations below.

Notes
~~~~~
.. _collision-notes:

* Collision Bounds are represented by a dashed line, unlike Bounds which are by solid lines. 

Collision Mapping
~~~~~~~~~~~~~~~~~
.. _collision-mapping:

* The following section describes the most appropriate primitive object to represent the desired collision object type.
* The suggested shapes also correspond to shapes generated through import by the plugin.
* On export the BhkShape is created from data pulled from the Collision object.

* Start by choosing a shape adequate to your model and follow the steps below the appropriate section.

**************rigid body needed, collision modifier also used but not needed?

Blender's Collision types map to the following Nif types:

- Oblivion, Fallout 3, and Fallout NV; 

+----------------------------+--------------------------------------------------------------+
| Blender                    | Nif                                                          |
+============================+==============================================================+
| `Box Collision`_           | :class:`~pyffi.formats.nif.NifFormat.bhkBoxShape`            |
+----------------------------+--------------------------------------------------------------+
| `Sphere Collision`_        | :class:`~pyffi.formats.nif.NifFormat.bhkSphereShape`         |
+----------------------------+--------------------------------------------------------------+
| `Capsule Collision`_       | :class:`~pyffi.formats.nif.NifFormat.bhkCapsuleShape`        |
+----------------------------+--------------------------------------------------------------+
| `Convex Hull Collision`_   | :class:`~pyffi.formats.nif.NifFormat.bhkConvexVerticesShape` |
+----------------------------+--------------------------------------------------------------+
| `Triangle Mesh Collision`_ | :class:`~pyffi.formats.nif.NifFormat.bhkMoppBvTreeShape`     |
+----------------------------+--------------------------------------------------------------+

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

#. Rename the prim-sphere, eg. 'CollisionSphere', via the Object panel

#. Scale the 'CollisionSphere' object as needed, ensuring all vertices are enclosed by the sphere

#. :ref:`Add physics to our 'CollisionSphere' <collison-settings>`.

Capsule Collision
~~~~~~~~~~~~~~~~~
.. _collision-capsule:

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create a second mesh-object to represent our collision object, a primitive cylinder(prim-cylinder) is recommended.

#. Rename the prim-cylinder via the Object panel, eg. 'CollisionCapsule'.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our 'CollisionCapsule' <collison-settings>`.

**Notes:**

.. _collision-capsule-notes:

* If the lenght is less than or equal to the radius, then a :class:`~pyffi.formats.nif.NifFormat.bhkSphereShape` is generated instead.

* Currently Capsule bounds lack viewport preview, awaiting Bullet Physic integration

* The following is a workaround; **Prone to user error, Ensure to reset setting after visualising!**.

 - In the **Object Tab**, under the **Display** section enable **Bounds**
 - Set the **Type** to **Cylinder**.
 
* This shape best represents the capsule, but visually missing the end caps which are hemi-spheres. 

Convex Hull Collision
~~~~~~~~~~~~~~~~~~~~~
.. _collision-convex-hull:

#. :ref:`Create your mesh-object <geometry-mesh>`. 

#. Create a convex mesh. See :ref:`Notes <collision-convex-hull-notes>`

#. Rename the hulled-object, eg. 'CollisionHull' via the Object panel.

#. Scale the collision cube 'CollisionBox' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

**Notes:**

.. _collision-convex-hull-notes:

* It is advisable to use a convex hull generator to create the collision-mesh.

Triangle Mesh Collision
~~~~~~~~~~~~~~~~~~~~~~~
.. _collision-triangle-mesh:

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create a convex hulled mesh-object. See :ref:`Notes<collision-convex-hull-notes>`

#. Rename the polyhedron-mesh, eg. 'CollisionPolyhedron' via the Object panel.

#. Scale the collision cube 'CollisionPoly' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collison-settings>`.

**Notes:**

.. _collision-triangle-mesh-notes:

* Often a duplicate object can be used, simplified by decimating, then triangulated(**Ctrl + T**).
* A :ref:`Convex Hulled Object<collision-convex-hull-notes>` can also be used.

Collision Settings
~~~~~~~~~~~~~~~~~~
.. _collison-settings:

* Meshes with Collision Bounds enabled will be exported as a :class:`~pyffi.formats.nif.NifFormat.bhkShape`, rather than a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* The Collision settings are used by the :class:`~pyffi.formats.nif.NifFormat.bhkShape` to control it reacts in the Havok physics simulation.

**Example:**

First we enable Collision Setting for the selected Collision Object:

* In the the **Physics** tab, enable **Collision Bounds** 

The bounds type is used to select which BhkShape type to use.

* Select the desired **Bounds** type from the dropdown box.

The Radius determines ???????????. Check if exporter reduces the radius for p.e. skyrim.

* Set the Radius to the appropriate number.

**************Velocity Max does not seem to be used in the nif.

The Collision Filter Flags determines ???????????. Skyrim's models all have this at 0, unsure about use in other games.

* Set the Col Filter to the appropriate number.

The Deactivator Type determines ???????????.

* Select a Deactivator Type from the dropdown box.

The Solver Deactivator determines ???????????.

* Select a Solver Deactivator from the dropdown box.

The Quality Type determines ???????????.

* Select a Quality Type from the dropdown box.

The Oblivion Layer determines ???????????.

* Select a Oblivion Layer from the dropdown box.

The Max Linear Velocity determines ???????????.

* Set the Max Linear Velocity to the appropriate number.

The Max Angular Velocity determines ???????????.

* Set the Max Angular Velocity to the appropriate number.

The Motion System determines ???????????.

* Select a Motion System from the dropdown box.

The Havok Material decides how the material should behave for collisions, eg. sound, decals.

* Select a Havok Material from the dropdown box.

The LHMaxFriction determines ???????????.

* Set the LHMaxFriction to the appropriate number.

The tau determines ???????????.

* Set the tau to the appropriate number.

The Damping determines ???????????.

* Set the Damping to the appropriate number.

.. todo::

   write up layer, quality type, motion system, etc.
   general workflow for creating collision



