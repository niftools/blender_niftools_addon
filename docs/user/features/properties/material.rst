
.. _properties-material:

Material Based Properties
-------------------------

* The following section goes through those Blender material settings and how they relate to corresponding nif blocks or
  attributes.
* Unless otherwise stated your mesh needs to have a material.
* The nif format only supports a single material per :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* A Mesh which contains multiple -materials will be exported as multiple
  :class:`~pyffi.formats.nif.NifFormat.NiTriShape`.
* Giving the Material an appropriate name helps distinguish materials and encourages reuse, eg. Metal, Glass, plastic
  etc.

Example
~~~~~~~

#. :ref:`Create a mesh-object <geometry-mesh>` as explained before.
#. In the **Properties** panel, in the **Material** tab click **New** to create a new material.
#. Assign the Material an appropriate name.

* :ref:`See material settings <properties-material-settings>` to see what material settings we use.

.. _properties-material-settings:

Blender Materials Settings
==========================

The following section describes which Blender Material setting we actively use.
Depending on the nif version you are exporting to, they will be mapped to different Nif block types or block
attributes.

Ambient
~~~~~~~

This is a global scene value; even if you use several materials they all share the same value.

#. In the **World Tab** -> **Ambient Color**.

* The diffuse colour dynamically calculated, so the value is not actually used.
* If you have found a nif that actually uses these values **please contact the
  devs** and we can enable per-material ambient.

Diffuse
~~~~~~~

#. In the **Diffuse** panel, click on the colour to bring up the colour widget

* Blender defaults is ``0.800``, which is off-white.
* See notes above why this value is defaulted on export.

Emissive
~~~~~~~~

This value sets how much light the material emits.

#. In the **Shading** panel is the Emissive colour
#. Set the **Intensity** value,

* Blender uses the diffuse colour for emission, viewable in the viewport.

.. 
   todo::
   add a preview button

Gloss
~~~~~

This value sets how diffuse the specular highlight across the material. Higher values of gloss(iness) mean that the
highlight is sharper/smaller.

#. In the **Surface** panel, deactivate the "Use Nodes" setting (setting the roughness of the BSDF node does nothing at
   the moment).
#. Set the **Roughness**. This is roughly the inverse of the gloss, calculated via roughness = 1/(gloss + 1)
#. Reactivate the "Use Nodes" setting. This is needed because otherwise the exporter needs nodes for textures etc.

Specular
~~~~~~~~

The Specular value creates the bright highlights that one would see on a glossy surface.

#. In the **Specular** panel, use the colour widget to set the highlight colour.
#. Set **Intensity** to whatever value you prefer. 


Alpha
~~~~~
The alpha component of the material is how much you can see through the material.

#. In the **Transparency** panel, **Enable Transparency**
#. Ensure **Z Transparency** is selected. (It should be by default).
#. Alter the **Alpha** setting. 