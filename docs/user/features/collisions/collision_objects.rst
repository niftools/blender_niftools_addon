Collision Object
----------------
.. _collisionobject:


The following section deals with creating an object which will physically
represent our collision object.


.. _collisionobject-mapping:

Collision Object Mapping
========================

* The following section describes the most appropriate primitive object to represent the desired collision object type.
* The suggested shapes are the same objects generated through import by the addon.
* Upon export, a collision object is created from data pulled from the Collision object.
* Start by choosing a shape adequate to your model and follow the steps below the appropriate section.

NiCollision
~~~~~~~~~~~

- Morrowind:

The following type use the collision bound type and the name to decide what to map to:

+-------------------+-------------------+
|      Blender      |    Object Name    |
+===================+===================+
| `Mesh Collision`_ | RootCollisionNode |
+-------------------+-------------------+
| `Bounding Box`_   | BSBound           |
+-------------------+-------------------+
| `Bounding Box`_   | BoundingBox       |
+-------------------+-------------------+

BhkShape
~~~~~~~~
- Oblivion, Fallout 3, and Fallout NV; 

+--------------------------+--------------------------------------------------------------+
|         Blender          |                             Nif                              |
+==========================+==============================================================+
| `Box Collision`_         | :class:`~pyffi.formats.nif.NifFormat.bhkBoxShape`            |
+--------------------------+--------------------------------------------------------------+
| `Sphere Collision`_      | :class:`~pyffi.formats.nif.NifFormat.bhkSphereShape`         |
+--------------------------+--------------------------------------------------------------+
| `Capsule Collision`_     | :class:`~pyffi.formats.nif.NifFormat.bhkCapsuleShape`        |
+--------------------------+--------------------------------------------------------------+
| `Convex Hull Collision`_ | :class:`~pyffi.formats.nif.NifFormat.bhkConvexVerticesShape` |
+--------------------------+--------------------------------------------------------------+
| `Mesh Collision`_        | :class:`~pyffi.formats.nif.NifFormat.bhkMoppBvTreeShape`     |
+--------------------------+--------------------------------------------------------------+

.. _collisionobject-bbox:

Bounding Box
^^^^^^^^^^^^

This is used as the bound box.

#. Create an Object of Mesh type to represent the bound box, a Cube is recommended.
#. Name the object BSBound or BoundingBox, depending on which version you need to be exported.
#. :ref:`Refer to the Collision Settings to add physics to our collision object <collisonsettings>`.

Visualisation

#. In the Object Tab, under the **Viewport Display** section update the **Display As** to `BOUNDS`.
#. Check the **Bounds** tickbox.
#. Select `BOX` from the **shape** dropdown.

Mesh Collision
^^^^^^^^^^^^^^

#. :ref:`Create your mesh-object <geometry-mesh>`.
#. Create a convex hulled mesh-object. See :ref:`Notes<collision-convex-hull-notes>`
#. Rename the polyhedron-mesh, eg. 'CollisionPolyhedron' via the Object panel.
#. Scale the 'CollisionPoly' to the size wanted.
#. :ref:`Refer to the Collision Settings to add physics to our collision object <collisonsettings>`.

Visualisation

#. In the Object Tab, under the **Viewport Display** section update the **Display As** to `BOUNDS`.
#. Check the **Bounds** tickbox.
#. Select `BOX` from the **shape** dropdown.

.. _collision-mesh-notes:

**Notes:**

* Often a duplicate object can be used, simplified by decimating, then triangulated(**Ctrl + T**).
* A :ref:`Convex Hulled Object<collision-convex-hull-notes>` can also be used.

.. _collisionobject-havok:

Havok Collision
===============

This is used by the havok system for collision detection.

.. General havok collision workflow -> add new object to serve as bounds .. (pretty much done) -> add rigid body [->
.. add collision ->] Define nif .. settings

.. warning::

   * For Cylinder Export, we need to fix them to show how the user would create the objects. We are using a Meta Capsule
   * Some of the collision types lack viewport rendering, see the workaround for visualisations below.

.. _collisionobject-notes:

Notes
~~~~~

* Collision Bounds are represented by a dashed line, unlike Bounds which are by solid lines.

.. _collisionobject-havokbox:

Box Collision
^^^^^^^^^^^^^

#. :ref:`Create your mesh-object <geometry-mesh>`.
#. Create a second mesh-object to represent our collision object, a primitive cube(prim-cube) is recommended.
#. Rename the prim-cube via the Object panel, eg. 'CollisionBox'
#. Scale the 'CollisionBox' uniformly to the size wanted.
#. :ref:`Add physics to our 'CollisionBox' <collisonsettings>`.

.. _collisionobject-havoksphere:

Sphere Collision
^^^^^^^^^^^^^^^^

#. :ref:`Create your mesh-object <geometry-mesh>`.
#. Create another mesh-object to represent our collision shape, a primitive sphere(prim-sphere) is highly recommended.
#. Rename the prim-sphere, eg. 'CollisionSphere', via the Object panel
#. Scale the 'CollisionSphere' object as needed, ensuring all vertices are enclosed by the sphere
#. :ref:`Add physics to our 'CollisionSphere' <collisonsettings>`.

.. _collisionobject-havokcapsule:

Capsule Collision
^^^^^^^^^^^^^^^^^

#. :ref:`Create your mesh-object <geometry-mesh>`.
#. Create a second mesh-object to represent our collision object, a primitive cylinder(prim-cylinder) is recommended.
#. Rename the prim-cylinder via the Object panel, eg. 'CollisionCapsule'.
#. Scale the collision cube 'CollisionBox' to the size wanted.
#. :ref:`Add physics to our 'CollisionCapsule' <collisonsettings>`.

.. _collision-capsule-notes:

**Notes:**

* If the length is less than or equal to the radius, then a :class:`~pyffi.formats.nif.NifFormat.bhkSphereShape` 
  is generated instead.
* Currently Capsule bounds lack viewport preview, awaiting Bullet Physic integration

* The following is a workaround; **Prone to user error, Ensure to reset setting after visualising!**.

  - In the **Object Tab**, under the **Display** section. Enable **Bounds**
  - Set the **Type** to **Cylinder**.
 
* This shape best represents the capsule, but visually missing the end caps which are hemispheres.

.. _collision-convex-hull:

Convex Hull Collision
^^^^^^^^^^^^^^^^^^^^^

#. :ref:`Create your mesh-object <geometry-mesh>`. 
#. Create a convex mesh. See :ref:`Notes <collision-convex-hull-notes>`
#. Rename the hulled-object, eg. 'CollisionHull' via the Object panel.
#. Scale the collision cube 'CollisionBox' to the size wanted.
#. :ref:`Add physics to our collision cube 'CollisionBox' <collisonsettings>`.

.. _collision-convex-hull-notes:

**Notes:**

* It is advisable to use a convex hull generator to create the collision mesh.

.. _collision-mesh:

