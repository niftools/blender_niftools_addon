.. _collisionobject:

Collision Object
----------------


.. warning::

   * This section has not been ported yet, meaning it does not currently work.

The following section deals with creating a mesh-object which will physically represent our collision object.
Once a suitable object has been created, then the appropriate settings should be enabled on 


.. _collisionobject-bbox:

Bounding Box
============

This is used as the bound box.

#. Create a Mesh-Object to represent the bound box, a Cube is recommended.

#. Name the object BSBound or BoundingBox, depending on which version you wish to be exported.

#. In the Object Tab, enable bounds in the display section.


.. _collisionobject-havok:

Havok Collision
===============

This is used by the havok system for collision detection.

.. General havok collision workflow -> add new object to serve as bounds (pretty much done) -> add rigid body [-> add collision ->] Define nif settings

.. warning::

   * For Cylinder Export, we need to fix them to show how the user would create the objects. We are using a Meta Capsule
   * Some of the collision types lack viewport rendering, see workaround for visulisations below.

.. _collisionobject-notes:

Notes
~~~~~

* Collision Bounds are represented by a dashed line, unlike Bounds which are by solid lines. 


.. _collisionobject-havokobject:

Collision Object
~~~~~~~~~~~~~~~~

* The following section describes the most appropriate primitive object to represent the desired collision object type.
* The suggested shapes are the same objects generated through import by the plugin.
* Upon export, a BhkShape is created from data pulled from the Collision object.
* Start by choosing a shape adequate to your model and follow the steps below the appropriate section.


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


* If the lenght is less than or equal to the radius, then a :class:`~pyffi.formats.nif.NifFormat.bhkSphereShape` is generated instead.

* Currently Capsule bounds lack viewport preview, awaiting Bullet Physic integration

* The following is a workaround; **Prone to user error, Ensure to reset setting after visualising!**.

 - In the **Object Tab**, under the **Display** section enable **Bounds**
 - Set the **Type** to **Cylinder**.
 
* This shape best represents the capsule, but visually missing the end caps which are hemi-spheres. 

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

* It is advisable to use a convex hull generator to create the collision-mesh.

.. _collision-triangle-mesh:

Triangle Mesh Collision
^^^^^^^^^^^^^^^^^^^^^^^

#. :ref:`Create your mesh-object <geometry-mesh>`.

#. Create a convex hulled mesh-object. See :ref:`Notes<collision-convex-hull-notes>`

#. Rename the polyhedron-mesh, eg. 'CollisionPolyhedron' via the Object panel.

#. Scale the collision cube 'CollisionPoly' to the size wanted.

#. :ref:`Add physics to our collision cube 'CollisionBox' <collisonsettings>`.

.. _collision-triangle-mesh-notes:

**Notes:**

* Often a duplicate object can be used, simplified by decimating, then triangulated(**Ctrl + T**).
* A :ref:`Convex Hulled Object<collision-convex-hull-notes>` can also be used.

.. _collisionobject-rigidbody:

Rigid Body
~~~~~~~~~~

.. small intro on what it is is needed. Maybe not needed since it is just mass

#. Go to the **Physics** tab in the **Properties** area.
#. Click on **Rigid Body** to enable this modifier.

   a) Set a mass adequate for your model.

.. _collisionobject-collmodifier:

Collision Modifier
~~~~~~~~~~~~~~~~~~

.. seems to be used in the code but no errors at export if not used - maybe not ported yet?
