.. _shader:

Shader
======

.. improve description

The following section describes the available shader options and their settings.

There are three different kinds of shader nodes:

   * *BS Shader PP Lighting Property*
   * *BS Lighting Shader Property*
   * *BS Effect Shader Property*

.. maybe use tables? will save a lot of scrolling

.. _shader-pplight:

BS Shader PP Lighting Property
------------------------------

.. Describe this type

This shader node is used for things.

* **Alpha Texture**
   Alpha Texture requires NiAlphaProperty to enable.

* **Decal Single Pass**
   Decal.

* **Dynamic Alpha**
   Dynamic Alpha.

* **Dynamic Decal Single Pass**
   Dynamic Decal

* **Empty**
   Unknown.

* **Environment Mapping**
   Environment Mapping (uses Envmap Scale).

* **External Emittance**
   External Emittance

* **Eye Environment Mapping**
   Eye Environment Mapping (does not use envmap light fade or envmap scale).

* **Face Gen**
   FaceGen.

* **Fire Refraction**
   Fire Refraction (switches on refraction power/period).

* **Hair**
   Hair.

* **Local Map Hide Secret**
   Localmap Hide Secret.

* **Low Detail**
   Low Detail (seems to use standard diff/norm/spec shader).

* **Multiple Textures**
   Multiple Textures (base diff/norm become null).

* **Non Projective Shadows**
   Non-Projective Shadows.

* **Parallax Occlusion**
   Parallax Occlusion.

* **Parallax Shader Index**
   Parallax.

* **Refraction**
   Refraction (switches on refraction power).

* **Remappable Textures**
   Usually seen with texture animation.

* **Shadow Frustum**
   Shadow Frustum.

* **Shadow Map**
   Shadow Map.

* **Single Pass**
   Single Pass.

* **Skinned**
   Required For skinned meshes.

* **Specular**
   Enables specularity.

* **Tree Billboard**
   Tree Billboard.

* **Unknown 1**
   Unknown.

* **Unknown 2**
   Unknown.

* **Unknown 3**
   Unknown/Crash.

* **Vertex Alpha**
   Vertex Alpha.

* **Window Environment Mapping**
   Window Environment Mapping.

* **Z-Buffer Test**
   Z-Buffer Test.



.. _shader-light:

BS Lighting Shader Property
---------------------------

.. Describe this type

Skyrim PP shader for assigning material/shader/texture.

This shader node is used for things.

* **Cast Shadows**
   Can cast shadows.

* **Decal**
   Decal.

* **Dynamic Decal**
   Dynamic Decal.

* **Environment Mapping**
   Environment mapping (uses Envmap Scale).

* **External Emittance**
   External Emittance.

* **Eye Environment Mapping**
   Eye Environment Mapping (Must use the Eye shader and the model must be skinned).

* **Facegen Detail**
   Use a face detail map in the 4th texture slot.

* **Facegen RGB Tint**
   Use tintmask for Face.

* **Fire Refraction**
   Fire Refraction.

* **Greyscale to Palette Alpha**
   Greyscale to Palette Alpha.

* **Greyscale to Palette Color**
   Greyscale to Palette Color.

* **Hair Soft Lighting**
   Keeps from going too bright under lights (hair shader only).

* **Landscape**
   Unknown.

* **Local map Hide Secret**
   Object and anything it is positioned above will not render on the local map view.

* **Model Space Normals**
   Use Model space normals and an external Specular Map.

* **Multiple Textures**
   Multiple Textures.

* **Non Projective Shadows**
   Unknown.

* **Own Emit**
   Provides its own emittance colour.

* **Parallax Occlusion**
   Parallax Occlusion.

* **Parallax**
   Parallax.

* **Projected UV**
   Used for decalling.

* **Receive Shadows**
   The object can receive shadows.

* **Refraction**
   Use normal map for refraction effect.

* **Remappable Textures**
   Remappable Textures.

* **Screendoor Alpha Fade**
   Screendoor Alpha Fade.

* **Skinned**
   Required For Skinned Meshes.

* **Soft Effect**
   Soft Effect.

* **Specular**
   Enables Specularity.

* **Temp Refraction**
   Unknown.

* **Use Falloff**
   Use Falloff value in EffectShaderProperty.

* **Vertex Alpha**
   Enables using the alpha component of vertex colours.

* **Z-Buffer Test**
   ZBuffer Test.

* **Anisotropic Lighting**
   Anisotropic Lighting.

* **Assume Shadowmask**
   Assume Shadowmask.

* **Back Lighting**
   Use Back Lighting Map.

* **Billboard**
   Billboard.

* **Cloud LOD**
   Cloud LOD.

* **Double Sided**
   Double-sided rendering.

* **Effect Lighting**
   Effect Lighting.

* **Envmap Light Fade**
   Envmap Light Fade.

* **Fit Slope**
   Fit Slope.

* **Glow Map**
   Use Glow Map in the third texture slot.

* **HD LOD Objects**
   HD LOD Objects.

* **Hide On Local Map**
   Similar to hide secret.

* **LOD Landscape**
   LOD Landscape.

* **LOD Objects**
   LOD Objects.

* **Multi-Index Snow**
   Multi-Index Snow.

* **Multi-Layer Parallax**
   Use Multilayer (inner-layer) Map.

* **No Fade**
   No Fade.

* **No LOD Land Blend**
   No LOD Land Blend.

* **No Transparency Multisampling**
   No Transparency Multisampling.

* **Packed Tangent**
   Packed Tangent.

* **Premult Alpha**
   Has Premultiplied Alpha.

* **Rim Lighting**
   Use Rim Lighting Map.

* **Soft Lighting**
   Use Soft Lighting Map.

* **Tree Anim**
   Enables Vertex Animation, Flutter Animation.

* **Uniform Scale**
   Uniform Scale.

* **Unused01**
   Unused.

* **Unused02**
   Unused.

* **Vertex Colors**
   Has Vertex Colors.

* **Vertex Lighting**
   Vertex Lighting.

* **Weapon Blood**
   Used for blood decals on weapons.

* **Wireframe**
   Wireframe.

* **Z-Buffer Write**
   Enables writing to the Z-Buffer.



.. _shader-effect:

BS Effect Shader Property
-------------------------

.. Describe this type

Skyrim non-PP shader model, used primarily for transparency effects, often as a decal.

* **Cast Shadows**
   Can cast shadows.

* **Decal**
   Decal.

* **Dynamic Decal**
   Dynamic Decal.

* **Environment Mapping**
   Environment mapping (uses Envmap Scale).

* **External Emittance**
   External Emittance.

* **Eye Environment Mapping**
   Eye Environment Mapping (Must use the Eye shader and the model must be skinned).

* **Facegen Detail**
   Use a face detail map in the 4th texture slot.

* **Facegen RGB Tint**
   Use tintmask for Face.

* **Fire Refraction**
   Fire Refraction.

* **Greyscale to Palette Alpha**
   Greyscale to Palette Alpha.

* **Greyscale to Palette Color**
   Greyscale to Palette Color.

* **Hair Soft Lighting**
   Keeps from going too bright under lights (hair shader only).

* **Landscape**
   Unknown.

* **Local map Hide Secret**
   Object and anything it is positioned above will not render on the local map view.

* **Model Space Normals**
   Use Model space normals and an external Specular Map.

* **Multiple Textures**
   Multiple Textures.

* **Non Projective Shadows**
   Unknown.

* **Own Emit**
   Provides its own emittance colour.

* **Parallax Occlusion**
   Parallax Occlusion.

* **Parallax**
   Parallax.

* **Projected UV**
   Used for decalling.

* **Receive Shadows**
   The object can receive shadows.

* **Refraction**
   Use normal map for refraction effect.

* **Remappable Textures**
   Remappable Textures.

* **Screendoor Alpha Fade**
   Screendoor Alpha Fade.

* **Skinned**
   Required For Skinned Meshes.

* **Soft Effect**
   Soft Effect.

* **Specular**
   Enables Specularity.

* **Temp Refraction**
   Unknown.

* **Use Falloff**
   Use Falloff value in EffectShaderProperty.

* **Vertex Alpha**
   Enables using the alpha component of vertex colours.

* **Z-Buffer Test**
   ZBuffer Test.

* **Anisotropic Lighting**
   Anisotropic Lighting.

* **Assume Shadowmask**
   Assume Shadowmask.

* **Back Lighting**
   Use Back Lighting Map.

* **Billboard**
   Billboard.

* **Cloud LOD**
   Cloud LOD.

* **Double Sided**
   Double-sided rendering.

* **Effect Lighting**
   Effect Lighting.

* **Envmap Light Fade**
   Envmap Light Fade.

* **Fit Slope**
   Fit Slope.

* **Glow Map**
   Use Glow Map in the third texture slot.

* **HD LOD Objects**
   HD LOD Objects.

* **Hide On Local Map**
   Similar to hide secret.

* **LOD Landscape**
   LOD Landscape.

* **LOD Objects**
   LOD Objects.

* **Multi-Index Snow**
   Multi-Index Snow.

* **Multi-Layer Parallax**
   Use Multilayer (inner-layer) Map.

* **No Fade**
   No Fade.

* **No LOD Land Blend**
   No LOD Land Blend.

* **No Transparency Multisampling**
   No Transparency Multisampling.

* **Packed Tangent**
   Packed Tangent.

* **Premult Alpha**
   Has Premultiplied Alpha.

* **Rim Lighting**
   Use Rim Lighting Map.

* **Soft Lighting**
   Use Soft Lighting Map.

* **Tree Anim**
   Enables Vertex Animation, Flutter Animation.

* **Uniform Scale**
   Uniform Scale.

* **Unused01**
   Unused.

* **Unused02**
   Unused.

* **Vertex Colors**
   Has Vertex Colors.

* **Vertex Lighting**
   Vertex Lighting.

* **Weapon Blood**
   Used for blood decals on weapons.

* **Wireframe**
   Wireframe.

* **Z-Buffer Write**
   Enables writing to the Z-Buffer.


.. _shader-lol:

.. BS Shader Property
.. -------------------------

.. It has no settings attached what is it for? 
