Features
========

.. todo::

   It would be a good habit to document every feature we have,
   and quick instructions for how to use them.

Collision
---------

To indicate that a mesh is to be exported as a collision object,
rather than say a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`,
select the blender **Game Engine** renderer, select the object's physics
tab, enable the **Collision Bounds** option, and select the desired
**Bounds**. For Oblivion, Fallout 3, and Fallout NV, blender's
collision types map to the following nif types:

============= ======================
blender       nif
============= ======================
Box           bhkBoxShape
Sphere        bhkSphereShape
Cylinder      bhkCapsuleShape
Capsule       bhkCapsuleShape
Convex Hull   bhkConvexVerticesShape
Triangle Mesh bhkMoppBvTreeShape
============= ======================

For Morrowind, we have:

============= =================
blender       nif
============= =================
Triangle Mesh RootCollisionNode
============= =================

.. todo::

   Where do we store material, layer, quality type, motion system, etc.?

Bounding Box
------------

.. todo::

   Write.
