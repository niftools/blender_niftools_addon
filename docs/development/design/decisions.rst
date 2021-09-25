.. _development-design-decisions:

################
Design Decisions
################

.. _development-design-decisions-geometrydata:

*************
Geometry Data
*************

.. _development-design-decisions-geometrydata-tangents:

Tangents
========

Tangents and bitangents are exported from Blender's tangents. This has two caveats:
* These are not the exact same as those of vanilla (Skyrim) assets.
* These tangents will only work completely correctly with normal maps that were generated with those tangents.
The first point is because we do not yet know by which method the vanilla tangents were generated. It is possible
that the generation method differs per model, and that there is no method which matches all vanilla models.

The second point is true for all tangent space normal maps. For more information on normal maps, see
`http://wiki.polycount.com/wiki/Normal_Map_Technical_Details#Tangent_Basis the polycount page`_. For information on how
the tangents get used in calculating surface direction, see
`http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/ the OpenGL tutorial`_. The main
characteristics that need to be the same between the renderer (the game) and the normal map baking software are:
* The tangent direction
* Whether the bitangent is calculated per-vertex or per-pixel (see
  `https://bgolus.medium.com/generating-perfect-normal-maps-for-unity-f929e673fc57#c473 this page`_).
Making sure that the tangent space is the same for the baker as it is in the nif is done by exporting a common
tangent space. The tangents from Blender are from `http://www.mikktspace.com/ MikkTSpace`_. This standard tangent space
is also an option in xNormal and Substance.

Because the bitangents are stored in the nif file, it can be assumed that they are not per-pixel in-game. Whether the
bitangent is calculated per-vertex or per-pixel is an option in xNormal and Substance. Blender calculates its bitangent
for baking per-pixel, which means that normal maps baked in Blender will not correctly display in-game, though the
difference may be minimal enough not to notice.

Blender tangent and bitangent to nif tangent and bitangent is not 1:1. In Blender, the tangent points in the positive U
direction and the bitangent points in positive V direction (Blender texture coordinates). In nifs, tangents point in
the positive V direction and bitangents point in the positive U direction (nif texture coordinates). Therefore, tangents
and bitangents are swapped between Blender and nif. However, because the nif V coordinate can be calculated from the
Blender V coordinate via::

    nif_V = 1 - blender_V

This means that the direction for positive V coordinate is reversed. This results in the conversion as follows.::

    nif_tangent = blender_bitangent
    nif_bitangent = blender_tangent