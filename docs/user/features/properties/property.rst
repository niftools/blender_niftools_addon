NiMaterialProperty
------------------
.. _properties-material:


The following section is for nifs which use :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.

* Material settings will alter how your Mesh will be rendered in-game.
* Every :class:`~bpy.types.Material` is exported to a :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.
* The nif format only supports a single material per :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* A Mesh which contains mult-materials will be exported as multiple :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* Giving the Material an appropriate name helps distingush materials and encourages reuse, eg. Metal, Glass, plastic etc.

Ambient
~~~~~~~

This is a global scene value; even if you use several materials they all share the same value.

#. In the **World Tab** -> **Ambient Color**.

* The diffuse color dynamically calculated, so the value is not actually used.
* If you have found a nif that actually uses these values please contact the devs and we can enable per material ambient.

Diffuse
~~~~~~~

#. In the **Diffuse** panel, click on the color to bring up the color widget

* Blender defaults is 0.800, which is off-white.
* See notes above why this value is defaulted on export.

Emissive
~~~~~~~~

This value sets how much light the material emit.

#. In the **Shading** panel is the Emissive color
#. Set the **Intensity** value,

* Blender uses the diffuse color for emission, viewable in the viewport.

.. TODO::
   add a preview button

Gloss
~~~~~

This value sets how diffuse the specular highlight across the material.

#. In the **Specular** panel
#. Set the **Hardness** 

* This value is used to set how intense the specular highlight should be.


NiSpecularProperty
------------------

.. _properties-specular:

The Specular value create the bright highlights that one would see on a glossy surface.

#. In the **Specular** panel, use the color widget to set the highlight color.
#. Set **Intensity** to whatever value you prefer. 

* Setting the **Intensity** to **0** will disable specularity; a :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty` will not be exported.

NiAlphaProperty
---------------

.. _properties-alpha:

The alpha component of the material is how much you can see through the material.

#. In the **Transparency** panel, **Enable Transparency**
#. Ensure **Z Transparency** is selected, which is by default.
#. Alter the **Alpha** setting. 

* An :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty` is exported for Materials or Texture have Alpha value.
   
   
NiWireFrameProperty
-------------------
.. _properties-wireframe:

:class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`

NiStencilProperty
-----------------
.. _properties-stencil:

The NiStencilProperty ignores the face normal and renders both sides of the mesh.

#. In the **Object Tab -> Double-Sided**, enable/disable.

* This will export a :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`

Notes
~~~~~

* Each triangle is composed of 3 vertices, edges and a face. This plane makes up the triangle.
* To decide which way the face is pointing a vector(normal), perpendecular to the face is used.
* The normal vector can be flipped to either side of the triangle; a common source for triangles appearing to not render correctly. 
* In-game if the camera is facing the normal then the face will be rendered.
* Otherside, it is not rendered and you will be able to look through the face.

.. TODO::
   
   Document these bad boys once implemented
   
   NiVertexColorProperty 
