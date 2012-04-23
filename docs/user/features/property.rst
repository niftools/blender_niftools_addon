Properties
==========
.. warning::
   The documentation are based on what features are mapped to blender.
   This will probably be rewritten with a general overview of the Blender Material settings and then relating back to property types.

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

.. todo::
   add a preview button
   
Notes
~~~~~

* A value of 0.0 will have no emit color
* Blender uses the diffuse color for viewport emission property.  

Gloss
~~~~~

We use the 

Notes
~~~~~


NiSpecularProperty
------------------

.. _properties-specular:

:class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty`,

#. In the **Specular** panel, use the color widget 
#. Set **Intensity** to whatever value you prefer. 

Notes
~~~~~

Setting the **Intensity** will to **0** disable specularity and a :class:`~pyffi.formats.nif.NifFormat.NiSpecularProperty` will not be exported.


NiAlphaProperty
---------------

.. _properties-alpha:

#. In the **Transparency** panel, **Enable Transparency**
#. Ensure **Z Transparency** is select, which is by default.
#. Alter the **Alpha** setting. 

An :class:`~pyffi.formats.nif.NifFormat.NiAlphaProperty` is used if the Material has an Alpha value.

Notes
~~~~~

This is also used by textures that use alpha.
   
   
NiWireFrameProperty
-------------------
.. _properties-wireframe:

:class:`~pyffi.formats.nif.NifFormat.NiWireframeProperty`,

NiStencilProperty
-----------------
.. _properties-stencil:

:class:`~pyffi.formats.nif.NifFormat.NiStencilProperty`,




.. todo::
   
   Document these bad boys once implemented
   NiVertexColorProperty 
