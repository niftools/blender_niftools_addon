Properties
==========
.. warning::
   This will probably be rewritten with a general overview of the Blender Material settings and then relating back to property types.
   This is due to different nif blocks sharing setting, NiMaterialProp, BSLightShaderProperty

* Most Nif properties, :class:`~pyffi.formats.nif.NifFormat.NiProperty` are mapped to some part of Blender's Material System.
* The following section goes through those Blender material settings and how they relate to those properties.
* Unless otherwise stated your mesh needs to have a material to use these properties.

Material
--------
.. _properties-material:

* Material settings will alter how your Mesh will be rendered.

Example
~~~~~~~

#. :ref:`Create a mesh-object <geometry-mesh>` as explained before.
#. In the **Properties** panel, in the *Material* tab
   click **New** to create a new material.
#. Assign the Material an appropriate name.
 
Notes
~~~~~

* Every :class:`~bpy.types.Material` is exported to a :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty`.
* The nif format only supports a single material per :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* A Mesh that contains mult-materials will be exported as multiple :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* Giving the Material an appropriate name will help distingush materials and encourages reuse, eg. Metal, Glass, plastic etc.

NiMaterialProperty
------------------
* The following section is for nifs which use :class:`~pyffi.formats.nif.NifFormat.NiMaterialProperty` and how it relates to Blender Material.

Ambient
~~~~~~~

The ambient color is actually located **World Tab** -> **Ambient Color**.
This is a global shared value; evenn if you use several materials they share the same value.

Notes
~~~~~
* Generally Nifs with NiMaterialProperty have the diffuse color dynamically calculated, so the value is not actually used.
* If you have found a nif that actually uses these values please contact the devs and we can enable per material ambient.

Diffuse
~~~~~~~
   
#. In the **Diffuse** panel, click on the color to bring up the color widget

Notes
~~~~~

   * Blender defaults is 0.800, which is off-white.
   * See notes above why this value is defaulted on export.

Emissive
~~~~~~~~

#. In the **Shading** panel is the Emissive color
#. Set the **Intensity** value   

Notes
~~~~~

* Blender uses the diffuse color for viewport emission property.  
.. todo::
   add a preview button

Gloss
~~~~~

* This value is used how intense the specular highlight should be.
* This will diffuse the specular across the material.

#. In the **Specular** panel
#. Set the **Hardness**  

Notes
~~~~~

* 


NiSpecularProperty
------------------

.. _properties-specular:

* The Specular value create the bright highlights that one would see on a glossy surface.

#. In the **Specular** panel, use the color widget to set the highlight color.
#. Set **Intensity** to whatever value you prefer. 

Notes
~~~~~

* Setting the **Intensity** to **0** will disable specularity; a :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty` will not be exported.

NiAlphaProperty
---------------

.. _properties-alpha:

* An :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty` is used if the Material has an Alpha value.


#. In the **Transparency** panel, **Enable Transparency**
#. Ensure **Z Transparency** is selected, which is by default.
#. Alter the **Alpha** setting. 

Notes
~~~~~

* The alpha component of the material is how much you can see through the material.
* This is property is also required when textures have alpha values.
   
   
NiWireFrameProperty
-------------------
.. _properties-wireframe:

:class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`,

NiStencilProperty
-----------------
.. _properties-stencil:

* If supported by the nif version, enabling **Double-sided** on a mesh-object will export a :class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`,
* The NiStencilProperty ignores the face normal and renders both sides of the mesh.
* See below for more details.

Notes
~~~~~

* A triangle is composed of 3 vertices, edges and a face. This plane makes up the triangle.
* To decide which way the face is pointing a vector(normal), perpendecular to the face is used.
* The normal vector can be flipped to either side of the triangle and is a common source of triangles/meshes not rendering. 
* In-game if the camera is facing the normal then the face will be rendered.
* Conversely if you are on the otherside, you usually will be able to look through the face as it is not rendered.
* Having the normal face the wrong direction is a common source 





.. todo::
   
   Document these bad boys once implemented
   NiVertexColorProperty 
