Mesh Geometry
-------------
.. _geometry-mesh:

* The following section deals with :class:`~bpy.types.Object` which are of type 'MESH', containing Mesh Data(Mesh-Object)
* Each :class:`~bpy.types.Object` is exported as a combination of :class:`~pyffi.formats.nif.NifFormat.NiTriShape` and :class:`~pyffi.formats.nif.NifFormat.NiNode`.
* The :class:`~bpy.types.Mesh` is exported to a :class:`~pyffi.formats.nif.NifFormat.NiTriShape`'s :class:`~pyffi.formats.nif.NifFormat.NiTriShapeData`.

**Example:**

#. Start Blender and empty the scene.
#. Create any Mesh-Object to the scene, eg. cube primitive: 

  - **Add(Shift + A) -> Mesh -> Cube**.

#. Set whether the Mesh-object should be Double-sided:
   
  - In the **Properties** Editor, in the **Object Data Tab**
  - Enable/Disable **Double Sided**, see notes for more detail.

#. Give the Object an appropriate name.

  - In the **Object Tab** 
  - Generic names are automatically generated, unique names helps distingush objects, 

#. Export the file: **File -> Export -> NetImmerse/Gamebryo**.

**Notes:**

* The Nif format only supports triangle based geometry.
* Blender quads and n-gons are exported as triangles, which may lead to differences in rendered geometry.
* Strips (:class:`~pyffi.formats.nif.NifFormat.NiTriStrips`) are available but not developer supported 
as they are `unnecessary for current hardware <http://tomsdxfaq.blogspot.com/2005_12_01_archive.html>`_.
* Double Sided Mesh - Adds a :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty` or similiar, 
see :ref:`Properties - Stencil Property <properties-stencil>` for more info.

UV Unwrapping
-------------
.. _geometry-uv:

* This is the process of unwrapping all the faces onto a flat surface, creating a UV Map layer.
* The UV Map layer is used to connect :class:`~bpy.types.Texture` to :class:`~bpy.types.Mesh`. 

**Example:**
#. :ref:`Create a mesh-object <geometry-mesh>`.
#. In **Edit Mode**, select the faces you want to unwrap.
#. Press U``, select **Unwrap > Smart UV Project**.

**Notes:**

* UV-unwrapping adds a :class:`~bpy.types.MeshTextureFaceLayer` to the Object.
* Althought Blender allows multiple :class:`~bpy.types.MeshTextureFaceLayer`, the Nif format only support one UV layer

Vertex Color
------------
.. _geometry-vertexcolor:

**Example:**

#. :ref:`Create a mesh-object <geometry-mesh>`.
#. Switch to Vertex Paint mode, this automatically adds a base vertex color layer.
#. Apply the desired vertex colors evenly to the vertex.
#. Ensure you have added a :ref:`material<properties-material>`.
#. Now export as usual.

**Notes:**

* The Nif format only supports a single color per vertex, whereas Blender vertex color per face vertex.
* Blender treats the vertex as if the faces had been split apart, each face can have a different color for that vertex.
* `This image should clarify per-face vertes coloring <http://i211.photobucket.com/albums/bb189/NifTools/Blender/documentation/per_face_vertex_color.jpg>`_
* On export the scripts will take an average of colors. 

.. warning::
   alpha layer support has been added but disabled due to known issues with general vertex color support.

.. todo::
   Write up workflow for alpha layer once implemented.
   