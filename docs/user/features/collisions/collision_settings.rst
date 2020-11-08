Collision Settings
------------------
.. _collisonsettings:

The following section details the setting which need to be applied to the
collision body to react appropriately in the collision simulation.

A lot of these setting are Havok-specific. We've mapped them to Blender's
collision simluation wherever possible.

.. _collisonsettings-enable:

Enabling Rigid Body Collisions
==============================

First, we enable Rigid Body Collision for the selected collision Object:

* In the **Physics** tab, click on **Rigid Body** to enable.

* Meshes with collision enabled will be exported as a collision object rather
  than a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.

#. Go to the **Physics** tab in the **Properties** area.

#. Click on **Rigid Body** to enable this modifier.

.. _collisionsettings-rigidbody:

Rigid Body Panel
================

.. _collisionsettings-havok:

The Rigid Body Panel is contains the properties to define how the object will
react in the physics simulation.

Settings Section
~~~~~~~~~~~~~~~~

**Mass** property used to give the collision object some weight

Collision Section
~~~~~~~~~~~~~~~~~

**Shape** is used to map to various collision types. The following table shows
*what they will map to. A combinaion of the type and Blender object name is used
to define the output type.

+----------------------------+---------------------+-----------------------------------------------------------+
|          Blender           | Blender Object Name |                            Nif                            |
+============================+=====================+===========================================================+
| `Triangle Mesh Collision`_ | RootCollisionNode   | :class:`~pyffi.formats.nif.NifFormat.NiNode.bounding_box` |
+----------------------------+---------------------+-----------------------------------------------------------+
| `Box Collision`_           | BSBound             | :class:`~pyffi.formats.nif.NifFormat.BSBound`             |
+----------------------------+---------------------+-----------------------------------------------------------+
| `Box Collision`_           | BoundingBox         | :class:`~pyffi.formats.nif.NifFormat.NiNode`              |
+----------------------------+---------------------+-----------------------------------------------------------+

- Oblivion, Fallout 3, and Fallout NV use bhk-based shapes

+----------------------------+--------------------------------------------------------------+
|          Blender           |                             Nif                              |
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

Surface Response Section
~~~~~~~~~~~~~~~~~~~~~~~~

In the **Surface Response** section the following are mapped to nif properties

- **Friction** : How smooth its surfaces is and how easily it will slide along
  other bodies

- **Restitution** : How "bouncy" the body is, i.e. how much energy it has after
  colliding. Less than 1.0 loses energy, greater than 1.0 gains energy.

Sensitivity Section
~~~~~~~~~~~~~~~~~~~

In the **Surface Response** section, enable the collsion margin.

- **Margin** : This is an area around the mesh that allows for quick but less
  accurate collision detection.

Dynamics Section
~~~~~~~~~~~~~~~~

In the **Surface Response** section, the following are mapped to nif
properties:

- **linear_damping** : Reduces the movement of the body over time. A value of
  0.1 will remove 10% of the linear velocity every second.

- **angular_damping** : Reduces the movement of the body over time. A value
of 0.05 will remove 5% of the angular velocity every second.

Enable the **Deactivation** checkbox to access the following settings:

- Deactivate Linear velocity : Linear velocity
- Deactivate Angular Velocity : Angular velocity

Custom Niftools Settings
========================

The following describe custom Nif-specific settings that don't map directly
to Blender settings currently:

.. todo::

    A lot of the items below need to be better-defined.

The **Havok Material** decides how the material should behave for collisions,
e.g., sounds, decals, etc.

* Select a **Havok Material** from the drop-down box.

The **Collision Filter Flags** determines...things.

* Set the **Col Filter** to the appropriate number.

The **Deactivator Type** determines...things

* Select a **Deactivator Type** from the drop-down box.

The **Solver Deactivator** determines...things.

* Select a **Solver Deactivator** from the drop-down box.

The **Quality Type** determines...things.

* Select a **Quality Type** from the drop-down box.

The **Oblivion Layer** determines...things.

* Select an **Oblivion Layer** from the drop-down box.

The **Max Linear Velocity** determines the maximum linear velocity this
collision object may have.

* Set the **Max Linear Velocity** to the appropriate number.

The **Max Angular Velocity** determines the maximum angular velocity this
collision object may have.

* Set the **Max Angular Velocity** to the appropriate number.

The **Motion System** determines...things.

* Select a **Motion System** from the drop-down box.
