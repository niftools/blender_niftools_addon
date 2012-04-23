Geometry
--------

Mesh Geometry
+++++++++++++

.. _geometry-mesh:

* Blender has a variety of Objects; the following section deals with object with Mesh Data(Mesh-Object)
* Each :class:`~bpy.types.Object` is exported to one or more :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* The :class:`~bpy.types.Mesh` is exported to the Objects :class:`~pyffi.formats.nif.NifFormat.NiTriShapeData`.

Example
~~~~~~~

#. Start blender with an empty scene.
#. Add any Mesh-Object to the scene, eg. cube primitive: **Add -> Mesh -> Cube**.
#. Select whether the Mesh-object should be Double-sided:
   
   * In the **Properties** panel, in the *Object Data* tab,
   * untick **Double Sided**.
   * This will add a :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`, see :ref:`Properties - Stencil Property <properties-stencil>` for more info.

#. Give the Object an appropriate name.
#. Export the file: **File -> Export -> NetImmerse/Gamebryo**.

Notes
~~~~~

* The nif format only supports triangle based geometry.
* Blender quads are exported as triangles, which may lead to differences in geometry rendered.
* Strips (:class:`~pyffi.formats.nif.NifFormat.NiTriStrips`) are available but developer support will be limited as they are `unnecessary for current hardware <http://tomsdxfaq.blogspot.com/2005_12_01_archive.html>`_.
* Naming individual objects helps distingush objects, generic names are automatically generated. eg. Cube, plane.001, sphere etc.

Vertex Color
++++++++++++

.. _geometry-vertexcolor:

#. :ref:`Create a single sided cube <geometry-mesh>` as explained before.
#. Switch to Vertex Paint mode, this automatically adds a base vertex color layer.
#. Apply the desired vertex colors evenly to the vertex.
#. Ensure you have added a material.
#. Now export as usual.

Notes
~~~~~

* The Nif format only supports a single color per vertex, whereas Blender vertex color per face vertex.
* Blender treats the vertex as if the faces had been split apart, each face can have a different color for that vertex.
* `Here is an example of per-face color <http://i211.photobucket.com/albums/bb189/NifTools/Blender/documentation/per_face_vertex_color.jpg>`_
* On export the scripts will take an average of colors. 

.. warning::
   alpha layer support has been added but enabled due to known issues with general vertex color support.

.. todo::
   Write up workflow for alpha layer once implemented.