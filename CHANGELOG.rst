Version v0.0.6
==============
- #431 Docs link not working
- #434 Update Sphinx docs theme
- #81 Add support for texture transforms
- #438 Cleanup of uv transform handling and texture slot name use, and change to glossiness import
- #437 Enable KF export
- #426 Minor animation export bugs fixed
- #420 Minor bugs in Kf Export
- #428 Updated shader import/export, mostly for BSShaderProperty
- #404 Export to Skyrim nif missing Has_Tangents bit

Version v0.0.5
==============
- #411 Usability : Niftool addon fails to install
- #424 Bug/fix operator menu registration
- #423 Update the release workflow to include the new update instructions.

Version v0.0.4
==============
- #410 Kf export
- #413 (Warped Mesh) Error on .nif import using Niftools Addon v0.0.3 in Blender 2.83 and Blender 2.91
- #417 Fix/export UI animation select registration
- #415 Added Kf export support for Skyrim
- #412 Re-enable animation export.

Version v0.0.3
==============
- #401 Consolidate scale correction value to be shared.
- #398 Animation - Imported animations with 'blank' keyframes containing no transformation
- #399 Animation - Fix fcurve data path
- #396 Usability - Improve logs to be more user friendly, remove stack traces
- #395 Bug - Exporting mesh with weight would cause execution to fail
- Fixed issue with .nif extension not being set on export
- Fixed issue with .kf being mapped to .egm
- #389 Docs - Updating Sphinx Documentation

Version v0.0.2
==============
- #390 Bug - Fixes bug where logging scale correction on export would cause execution to fail

Version v0.0.1
==============

- Rename plugin to use new naming scheme
- Add in updated templates
- Add in auto-updater to allow addon to fetch releases and upgrade from within user preferences




.. note::
    The following are older versions, using the old naming scheme

Version 2.6.0.adev4
===================

Features
--------

+--------+------------------------------------------------------------------------------------------------------------+
| Ticket |                                                Description                                                 |
+========+============================================================================================================+
| 361    | Feature: Import Pose                                                                                       |
+--------+------------------------------------------------------------------------------------------------------------+
| 353    | Automatically select suitable axis orientation                                                             |
+--------+------------------------------------------------------------------------------------------------------------+
| 11     | Billboard support                                                                                          |
+--------+------------------------------------------------------------------------------------------------------------+
| 15     | Vertex Alpha prop support                                                                                  |
+--------+------------------------------------------------------------------------------------------------------------+
| 25     | `` NiAlphaProperty`` detection for textures                                                                |
+--------+------------------------------------------------------------------------------------------------------------+
| 288    | material export: alpha                                                                                     |
+--------+------------------------------------------------------------------------------------------------------------+
| 346    | Port/collision game radius                                                                                 |
+--------+------------------------------------------------------------------------------------------------------------+
| 342    | Update documentation for 2.8 + mat sys improvements                                                        |
+--------+------------------------------------------------------------------------------------------------------------+
| 337    | Refactor/blender 2.8 ui registration                                                                       |
+--------+------------------------------------------------------------------------------------------------------------+
| 335    | Merge/version string                                                                                       |
+--------+------------------------------------------------------------------------------------------------------------+
| 329    | Port to 2.8+                                                                                               |
+--------+------------------------------------------------------------------------------------------------------------+
| 324    | Addon enabled in Blender 2.82.7, Option to Import and Export .NIF Files not appearing under File``         |
+--------+------------------------------------------------------------------------------------------------------------+
| 310    | Fix Morph Anims (NiGeomMorpherController)                                                                  |
+--------+------------------------------------------------------------------------------------------------------------+
| 311    | Anim stuff                                                                                                 |
+--------+------------------------------------------------------------------------------------------------------------+
| 282    | Documentation Improvement                                                                                  |
+--------+------------------------------------------------------------------------------------------------------------+
| 287    | Animation Import Support                                                                                   |
+--------+------------------------------------------------------------------------------------------------------------+
| 289    | New bone system (no extra matrices) & animation support                                                    |
+--------+------------------------------------------------------------------------------------------------------------+
| 299    | Format UI & Operator Modules                                                                               |
+--------+------------------------------------------------------------------------------------------------------------+
| 257    | - allow exporting of object while ignoring non-uv textures                                                 |
|        | - Unable to export an object with non-uv textures without either deleting the textures or first creating a |
|        |   UV-map for them.                                                                                         |
|        | - Updated NifError to NifLog.warn: nothing here should prevent you from exporting objects so long as the   |
|        |   user is aware of what is happening.                                                                      |
|        | - The messages themselves were updated to be more helpful.                                                 |
+--------+------------------------------------------------------------------------------------------------------------+

Bug Fixes
---------

+--------+-----------------------------------------------------------------------------------------------------------+
| Ticket |                                                Description                                                |
+========+===========================================================================================================+
| 378    | Bug fixes to zip generation, BSEffecShaderProperty export, and meshes parented to armature. Also game set |
|        | on import.                                                                                                |
+--------+-----------------------------------------------------------------------------------------------------------+
| 377    | Update transform.py                                                                                       |
+--------+-----------------------------------------------------------------------------------------------------------+
| 376    | Update __init__.py                                                                                        |
+--------+-----------------------------------------------------------------------------------------------------------+
| 369    | Fix to bhkBoxShape and bhkSphereShape translation export and  documentation                               |
+--------+-----------------------------------------------------------------------------------------------------------+
| 368    | Fix to bhkBoxShape and bhkSphereShape translation                                                         |
+--------+-----------------------------------------------------------------------------------------------------------+
| 365    | Bug/export disable clamp mode                                                                             |
+--------+-----------------------------------------------------------------------------------------------------------+
| 276    | Error when exporting material with texture without UV                                                     |
+--------+-----------------------------------------------------------------------------------------------------------+
| 350    | Cannot import Skeleton to Fallout New Vegas                                                               |
+--------+-----------------------------------------------------------------------------------------------------------+
| 363    | Fix/bss shader node setup                                                                                 |
+--------+-----------------------------------------------------------------------------------------------------------+
| 357    | Messed up skeleton weights & some vertices not loaded                                                     |
+--------+-----------------------------------------------------------------------------------------------------------+
| 362    | Fix/bss shader reference                                                                                  |
+--------+-----------------------------------------------------------------------------------------------------------+
| 359    | Fixes to BSLightingShaderProperty                                                                         |
+--------+-----------------------------------------------------------------------------------------------------------+
| 354    | ReferenceError: StructRNA of type Image has been removed                                                  |
+--------+-----------------------------------------------------------------------------------------------------------+
| 349    | Collision fixes and stuff                                                                                 |
+--------+-----------------------------------------------------------------------------------------------------------+
| 172    | Mesh Export : Unweighted vertices                                                                         |
+--------+-----------------------------------------------------------------------------------------------------------+
| 328    | ValueError: deepcopy: classes BSFadeNode and NiTriShape unrelated                                         |
+--------+-----------------------------------------------------------------------------------------------------------+
| 331    | Cannot Export Skyrim Skeleton                                                                             |
+--------+-----------------------------------------------------------------------------------------------------------+
| 243    | Assertion Error : f_numverts == 3 or 4                                                                    |
+--------+-----------------------------------------------------------------------------------------------------------+
| 255    | Ngon Fixes                                                                                                |
+--------+-----------------------------------------------------------------------------------------------------------+
| 341    | Merge #340 to 2.8 Bug BSEffectShaderProperty shader controller                                            |
+--------+-----------------------------------------------------------------------------------------------------------+
| 347    | Merge/bs effect shader missing texture fix                                                                |
+--------+-----------------------------------------------------------------------------------------------------------+
| 344    | Incorrect import of greyscale texture for BSEffectShaderProperty                                          |
+--------+-----------------------------------------------------------------------------------------------------------+
| 343    | Error when exporting BSEffectShaderProperty without textures                                              |
+--------+-----------------------------------------------------------------------------------------------------------+
| 339    | Error importing BSEffectShader without Controller.                                                        |
+--------+-----------------------------------------------------------------------------------------------------------+
| 336    | Merge/bug fix collision bhk mopp list processing                                                          |
+--------+-----------------------------------------------------------------------------------------------------------+
| 333    | Fix collision import processing for bhkMoppBVTreeShape & bhkListShape                                     |
+--------+-----------------------------------------------------------------------------------------------------------+
| 330    | Export Zoo Tycoon 2 Error                                                                                 |
+--------+-----------------------------------------------------------------------------------------------------------+
| 244    | UI : Property not found: ShaderProps.slsf_1_greyscale_to_palettecolor                                     |
+--------+-----------------------------------------------------------------------------------------------------------+
| 321    | Fallout 3/new vegas materials import                                                                      |
+--------+-----------------------------------------------------------------------------------------------------------+
| 320    | can't import / export Skyrim nifs                                                                         |
+--------+-----------------------------------------------------------------------------------------------------------+
| 325    | Refactor Collision Export                                                                                 |
+--------+-----------------------------------------------------------------------------------------------------------+
| 242    | Export : UV offset not found                                                                              |
+--------+-----------------------------------------------------------------------------------------------------------+
| 260    | Shaders : texprop.shader_textures[1] index error                                                          |
+--------+-----------------------------------------------------------------------------------------------------------+
| 312    | Fix collision / havok materials & pyffi dev compatibility                                                 |
+--------+-----------------------------------------------------------------------------------------------------------+
| 308    | Refactor/animation Bug Error                                                                              |
+--------+-----------------------------------------------------------------------------------------------------------+
| 283    | Fixed CONTRIBUTING.rst grammar mistake                                                                    |
+--------+-----------------------------------------------------------------------------------------------------------+
| 264    | - import and export Morrowind collision nodes properly                                                    |
|        | - name of the node be RootCollisionNode to properly export it, but the importer called it instead just    |
|        | "collision"                                                                                               |
+--------+-----------------------------------------------------------------------------------------------------------+
| 256    | - check that selected objects can be exported                                                             |
|        | - UnboundLocalError: local variable 'root_object' referenced before assignment                            |
+--------+-----------------------------------------------------------------------------------------------------------+
| 252    | armature and version export                                                                               |
|        | Refactored code fails on armature export                                                                  |
|        | Value for version not assigned, fails export                                                              |
|        | - AttributeError: 'NifExport' object has no attribute 'version'                                           |
+--------+-----------------------------------------------------------------------------------------------------------+
| 242    | Export : UV offset not found                                                                              |
+--------+-----------------------------------------------------------------------------------------------------------+
| 251    | - TypeError: load_nif() missing 1 required positional argument: 'file_path'                               |
|        | - AttributeError: 'NifExport' object has no attribute 'set_object_matrix'                                 |
+--------+-----------------------------------------------------------------------------------------------------------+
| 275    | Fix Addon Documentation and Bug Tracker links                                                             |
+--------+-----------------------------------------------------------------------------------------------------------+
| 274    | Links in the addon direct to the wrong urls                                                               |
+--------+-----------------------------------------------------------------------------------------------------------+
| 265    | Submodules not getting included by makezip.bat                                                            |
+--------+-----------------------------------------------------------------------------------------------------------+

Internal
--------

+--------+-----------------------------------------------------------------+
| Ticket |                           Description                           |
+========+=================================================================+
| 355    | Fixes to the installation bat files                             |
+--------+-----------------------------------------------------------------+
| 152    | Material code improvements                                      |
+--------+-----------------------------------------------------------------+
| 332    | Change the version string                                       |
+--------+-----------------------------------------------------------------+
| 322    | Refactor/shader code                                            |
+--------+-----------------------------------------------------------------+
| 319    | Refactor/split import export modules                            |
+--------+-----------------------------------------------------------------+
| 318    | Refactor/object mesh heirarchy                                  |
+--------+-----------------------------------------------------------------+
| 316    | Refactor/texture property                                       |
+--------+-----------------------------------------------------------------+
| 315    | Refactor mesh code from nif_import                              |
+--------+-----------------------------------------------------------------+
| 313    | Refactor Object & Mesh property handling                        |
+--------+-----------------------------------------------------------------+
| 307    | Several fixes for refactor/object_type                          |
+--------+-----------------------------------------------------------------+
| 306    | Refactor/object type Improvement Restructure                    |
+--------+-----------------------------------------------------------------+
| 305    | Refactor/block registry Improvement                             |
+--------+-----------------------------------------------------------------+
| 304    | Refactor/pep pass Improvement                                   |
+--------+-----------------------------------------------------------------+
| 303    | Refactor/utils Improvement                                      |
+--------+-----------------------------------------------------------------+
| 301    | Refactoring / fixes for pyffi/nifxml upgrades                   |
+--------+-----------------------------------------------------------------+
| 303    | Refactor/utils                                                  |
+--------+-----------------------------------------------------------------+
| 298    | Refactor/build system                                           |
+--------+-----------------------------------------------------------------+
| 295    | Formatting Animation & Armature modules.                        |
+--------+-----------------------------------------------------------------+
| 296    | Refactor/formatting collision modules                           |
+--------+-----------------------------------------------------------------+
| 297    | Update testframework with pep8 updates and new module structure |
+--------+-----------------------------------------------------------------+
| 278    | Remove external dependencies needed to build                    |
|        | - Remove the reliance on buildenv                               |
|        | - Remove need to install zip on windows                         |
+--------+-----------------------------------------------------------------+
| 277    | Migrated modules from root folder                               |
+--------+-----------------------------------------------------------------+
| 273    | Template updates                                                |
+--------+-----------------------------------------------------------------+
| 267    | Hosted docs                                                     |
+--------+-----------------------------------------------------------------+
| 270    | Change submodule and sourceforge links                          |
+--------+-----------------------------------------------------------------+
| 208    | Pyffi submodule                                                 |
+--------+-----------------------------------------------------------------+
| 217    | Document update                                                 |
+--------+-----------------------------------------------------------------+

Version 2.6.0a3 (3 Jan 2015)
============================

* Migrated to Bmesh API

* Fix UV layer detection

* Additional material properties support (alpha, specular, stencil, wire).

* Add support for NiTexturingProperty (diffuse, bump, normal map, specular and glow).

* Fix crash when combine shapes are enabled (reported and fix contributed by Aaron1178)

* Fix issue with material texture blend type importing (reported and fix contributed by mgm101).

* Added experimental vertex color support.

* Collision support:
  - Basic BhkShapes Cube, Sphere, Cylinder.
  - Convex Vertex, NiPacked, NiTriStrips Shapes.
  - Bound Box support.

* Subsystem separation (collision, armature, material, texture).

* Bundle PyFFI with scripts.

* Distribute zip that can be used with Blender's built-in installer.

* Extensive work on the testing framework:
  - Tests created based on new features.
  - Re-organised tests into per feature, generated test nifs.
  - Inheritance based checks now functioning.

* Documentation vastly improved.
   - Feature documentation
   - Developer documentation, API auto-doc and workflow
   

Version 2.6.0a0 (20 Nov 2011)
=============================

* Initial port to Blender 2.60a:
  - geometry (NiTriShape)
  - materials (NiMaterialProperty)
  - UV textures (NiTexturingProperty)

* Upgraded to sphinx to generate documentation.

* Upgraded to nose for testing.

Version 2.5.8 (30 Oct 2011)
===========================

* Fix for collision objects that have no vertices (see issue #3248754, reported by rlibiez).

* Fix for export of convex collision shapes bundled together in a list (see issue #3308638, reported by Koniption).

* Updated installer to get the Blender 2.49b installer if Blender is not yet installed (this avoids confusion with
  Blender 2.5x+ being the default on the official download page).

Version 2.5.7 (26 March 2011)
=============================

* added rubber material (reported by Ghostwalker71)

* havok material name bugfix

* fixed issue with dysfunctional havok constraints in ANIM_STATIC, CLUTTER, and BIPED layers (reported and fix
  contributed by Koniption)

* also import BSBound bounding box on dummy scene node

* fixed BSBound import and export scale (see issue #3208935, reported and fix contributed by neomonkeus)

Version 2.5.6 (4 February 2011)
===============================

* fix import in case skin instance has empty bone references (fixes PyFFI issue #3114079, reported by drakonnen)

* updated for PyFFI 2.1.8

* fix export of bezier curve animation (reported by arcimaestro)

* split multi-material mopps into different NiNodes so we only have single material mopps; this works around the usual
  mopp issues (reported by neomonkeus)

* new export option for Bully SE; sane settings are automatically selected

* improved support for Divinity 2 nifs (reported by pertinen)

Version 2.5.5 (18 July 2010)
============================

* fixed bone priority import for L and R bones (reported by Da Mage)

* updated for PyFFI 2.1.5

* fixed NiCollisionData import (reported by LordOfDragons)

Version 2.5.4 (28 Mar 2010)
===========================

* fixed bone priority export for L and R bones (reported by Kilza)

* fixed morph base key name import (reported by LHammonds)

* fixed morph base key to having no float data (reported by LHammonds)

* improved export of controller start and stop times (reported  by LHammonds)

* fixed consistency type on NiGeometryData to be CT_VOLATILE when exporting morphs; this fixes for instance bow exports
  (reported and fix suggested by LHammonds, based on Nicoroshi and Windy's bow tutorials)

Version 2.5.3 (19 Mar 2010)
===========================

* import and export NiLODNodes as empty with LODs as children and properties to set extents

* added material colour controller import and export (request and test files by Alphax)

* added vis controller import and export (request and test files by Alphax)

* fixed some controller imports in case controller block had no data

* improved Fallout 3 skeleton.nif import

* fixed bhkCapsuleShape export with identical points by converting it to a bhkSphereShape (reported by ghostwalker71)

* warn if mopp is exported for non-static objects, as these may not function properly in-game (reported by mc.crab)

* added an option to use NiBSAnimationNode when exporting animated branches for Morrowind (suggested and tested by
  TheDaywalker)

Version 2.5.2 (20 Feb 2010)
===========================

* configurable game paths for test suite

* fixed display of alpha channel in textured faces (reported by vurt2, fixed by Alphax)

* The weight squash script can now limit the number of bone influences per vertex (requested by Growlf)

* disabling combine shapes import option results in xbase_anim type nifs to import clothing slots as bones (fixes
  transform issue reported by Arcimaestro Anteres)

* added regression test and workaround for duplicate shape keys during import: only the first is read, and duplicates
  are ignored (e.g. Fallout 3 skeleton.nif HeadAnims:0)

* added regression test and workaround for corrupt translation keys in Fallout 3 interpolators (e.g. Fallout 3
  h2haim.kf, reported by Malo)

* added experimental .kf export for Freedom Force and Freedom Force vs. the 3rd Reich

* fixed interpolator bug with bhkBlendControllers when exporting kf files for creatures with bones that have havok
  blocks attached (reported by Spiderpig)

* added alpha controller import; export was already implemented (requested and test files provided by Alphax)

* fixes/improvements to animation import and export
  - full support for import/export of animation priority
  - autoset target name to bip02 if the armature has such a bone
  - new option to manually set the target name on export
  - new option to bulk set the animation priority
  - skip NiBSplineInterpolators on import; not fully supported and
    if not skipping was causing a fatal error

* fix for bhkNiTriStripsShape import

* added experimental import and export of Empire Earth II meshes

* fixed bhkCapsuleShape import with identical points (reported by
  ghostwalker71)

Version 2.5.1 (10 Jan 2010)
===========================

* updated for PyFFI 2.1.0

* fixed stencil property export for Fallout 3

* Morrowind bounding box import and export

* import and export, via object properties per object, of havok object
  - material
  - collision layer
  - motion quality
  - motion system
  - mass
  - col filter

* import and export, via object properties per object, of havok constraint
  - min angle
  - max angle
  - friction

* object rotation animation import bugfix (reported by Arcimaestro Anteres, fixes, for instance, Morrowind animated
  creature imports)

* fix for Fallout 3 NiGeomMorpherController (shape key) export (reported by Bleolakri)

* pep8 fixes

* The installer detects Python 64 bit and complains about it

* increased resolution of vertex coordinates to 1/1000 (from 1/200) on import and export (fixes issue #2925044 reported
  by EuGENIUS).

* added support for Atlantica and Howling Sword import and export

Version 2.5.0 (22 Nov 2009)
===========================

* attempt to fix invalid matrices in bone extra text buffer rather than raising a mysterious exception (reported by
  PacificMorrowind)

* import and export Oblivion morph controller animation data (reported by LHammonds, additional testing and bug reports
  by PacificMorrowind)

* import extra nodes as empties

* extra nodes are now imported by default (suggested by PacificMorrowind)

* various object animation import and export fixes (reported by LHammonds and Tijer)

* enable flattening skin in the export GUI when 'geometry only' is selected, for Oblivion and Fallout 3 (contributed by
* PacificMorrowind)

* civ4 and Sid Meier's Railroads NiNode and NiTriShape flags are now set to 16 (reported by Tijer)

* on import, set alpha to 0.0 if NiAlphaProperty is present (so it gets re-exported) even if no textures with alpha
  channel are found; this fixes an issue with Sid Meier's Railroads (reported by Tijer)

* export NiAlphaProperty threshold 150 for Sid Meier's Railroads (reported by Tijer)

* export RRT_NormalMap_Spec_Env_CubeLight shader for Sid Meier's Railroads (reported by Tijer)

* force TSpace flag to be 16 for Sid Meier's Railroads and Fallout 3 (reported by Tijer and Miaximus)

* fixed windows installer & installer scripts to install to the dirs currently expected by Blender (contributed by
  PacificMorrowind)

* import and export EGM morphs (with aid of Scanti and Carver13)

* added new experimental "morph copy" script (under scripts->mesh)

* stitch strips for Fallout 3 by default (reported by Miaximus)

* fixed texture path bug (reported by elitewolverine)

Version 2.4.12 (23 Oct 2009)
============================

* warn and ignore object animation on skinned meshes, instead of raising a mysterious exception (reported by vfb)

* added Zoo Tycoon 2 .kf export

* added dialogue requesting animation sequence name for .kf export (contributed by PacificMorrowind)

* added preset for Oblivion OL_ANIM_STATIC objects (see issue #2118370 exported by apwsoft; fix discovered by
  PacificMorrowind)

* Export XYZ rotations for object animations instead of converting to quaternions (reported by Artorp)

* set the bhkCollosionObject flag to 41 instead of the default 1 for animated (OL_ANIM_STATIC) objects (reported by
  Artorp)

* updated readme with detailed install instructions

Version 2.4.11 (28 Sep 2009)
============================

* added NeoSteam import and export support

* warn on corrupt rotation matrix, rather than raising an exception

* bug fix in case (corrupt) root block has no name attribute

* fix for collision export with very small mass (contributed by PacificMorrowind, see issue #2860536)

Version 2.4.10 (22 Jul 2009)
============================

* Windows installer updated for Python 2.6 and PyFFI 2.0.1.

* set affected node list pointer on Morrowind environment map (contributed by Alphax)

* use Blender's texture dir on import (contributed by puf_the_majic_dragon)

Version 2.4.9 (20 Jun 2009)
===========================

* test and fix for NiKeyframeController target in Morrowind xkf files (reported by arcimaestro, see issue #2792951)

* test and fix for NiKeyframeController flags import and export: the nif cycle mode is mapped onto the Blender IPO
  curve extrapolation mode (reported by arcimaestro, see issue #2792951)

* test and fix for animation buffer out of range exception - the exporter will now only warn about it but continue with
  export anyway (reported by rcimaestro, see issue #2792952)

* fixed bug when importing extra bones which were parented on a grouping bone (for instance Morrowind
  atronach_frost.nif, where Bone01 is parented to Weapon, which groups the geometry Tri Weapon)

Version 2.4.8 (3 Jun 2009)
==========================

* fixed bug in hull script (reported by Drag0ntamer, fixed by Alphax)

Version 2.4.7 (4 May 2009)
==========================

* fixed bug where "apply skin deform" would apply it more than once on geometries that are linked to more than once in
  the nif

* new option to import extra nodes which are not bone influences as bones (reported by mac1415)

* bugfix for Euler type animation import

* max bones per partition now default to 18 for civ4 (reported by mac1415)

* updated for PyFFI 2.0.0

* moved advanced import settings to the new column (reported by Alphax)

* inverted X and Y offset UV Ipo channels on import and export (reported by Alphax)

* added support for civ4 shader textures (reported by The_Coyote)

* new option to control the export of extra shader textures for civ4 and sid meier's railroads (reported by The_Coyote)

* if extra shader textures are exported, then tangent space is generated (reported by The_Coyote)

* fixed scaling bug if the scale was not 1.0 in certain cases (such as civ4 leaderheads, reported by The_Coyote)

* realign bone tail only is now the import default (slightly better visual representation of bones in complex armatures
  such as civ4 leaderheads)

Version 2.4.6 (23 Apr 2009)
===========================

* import and export of Morrowind NiUVController/NiUVData i.e. moving textures (with help from Axel, TheDaywalker, and
  Alphax)

Version 2.4.5 (21 Apr 2009)
===========================

* another import fix for names that end with a null character

* warn on packed textures instead of raising an error (reported by augbunny)

* Morrowind:
  - rebirth of the 'nif + xnif + xkf' option for Morrowind (reported by axel)
  - improved import of nifs that have multiple skeleton roots (such as the official skin meshes, and various
    creatures such as the ice raider)
  - new import option to merge skeleton roots (enable!)
  - new import option to send detached geometries to node position (enable!)

* Fallout 3:
  - now imports and exports the emitMulti value in the shader emit slider (up to a factor 10 to accommodate the
    range) and stores the emissive colour as Blender's diffuse colour (reported and tested by mushin)
  - glow texture import and export (reported and tested by mushin)

Version 2.4.4 (2 Apr 2009)
==========================

* import option to disable combining of shapes into multi-material meshes (suggested by Malo, and contributed by Alphax)

* Importing a nif with an unsupported root block now only gives an error message instead of raising an exception
  (reported by TheDaywalker)

* fixed Fallout 3 import of packed shapes (such as mopps)

Version 2.4.3 (7 Mar 2009)
==========================

* further fixes for Fallout 3
  - new options in the export dialogue for shader flags and shader type (thanks to malo and nezroy)
  - new option to disable dismember body part export (sickleyield)

* text keys imported also if they are not defined on the scene root (reported by figurework)

Version 2.4.2 (15 Feb 2009)
===========================

* materials whose name starts with "noname" (such as those that are imported without a name) will have no name in the
  nif; this fixes some issues with Fallout 3 (reported by malo)

* import fix for names that end with a null character (reported by alphax)

* if not all faces have a body part, they will be selected on export to make it easier to identify them; error message
  has been improved too (reported by malo)

* meshes without vertices are skipped; so they no longer give a mysterious error messages (reported by malo)

Version 2.4.1 (2 Feb 2009)
==========================

* Fallout 3 BSShaderXXX blocks are no longer shared to avoid issues with the engine

* NiSourceTexture improvements:
  - pixel layout exports as "6" (DEFAULT) for versions 10.0.1.0 and higher
  - use mipmaps exports as "1" (YES)

* Sid Meier's Railroads:
  - new regression test
  - fixed import and export of specular colour
  - fixed alpha flags export
  - automatic integer extra data export for shader texture indices
  - automatic export of RRT_Engine_Env_map.dds and RRT_Cube_Light_map_128.dds shader texture slots
  - import of extra shader textures, using extra integer data to find the right texture slot
  - bump (i.e. normal), gloss (i.e. spec), and reflection (i.e. emsk) are exported into the extra shader slots
    instead of in the regular slots

* minor cleanups in the code

Version 2.4.0 (25 Jan 2009)
===========================

* switched to using the standard logging module for log messages

* improvements for multi-material mopp import and export (but not entirely functional yet)

* improved self-validating bind position algorithm
  - geometries are transformed first to a common bind pose (if it exists, a warning is issued if no common bind pose
    is found) - some misaligned geometry pieces will now be aligned correctly with the armature, this is most notably
    with Morrowind imports
  - bone nodes are transformed to bind position in two phases, to reduce rounding errors - some bones that were not
    sent to the bind pose with the older algorithm will now be correct

* better Fallout 3 export options

* added export of Fallout 3 tangent space

* added export of Fallout 3 BSShaderPPLightingProperty for textures

* body parts can now be imported and exported via vertex groups

* fixed RuntimeError when importing mesh without faces

Version 2.3.13 (18 Nov 2008)
============================

* better error message if the mesh has bone vertex group but no weights

* improved Civ IV bone flags export (0x6 for intermediate bones, 0x16 for final ones)

* support for double-sided meshes via NiStencilProperty and Blender's double sided flag

* NiAlphaProperty flags now defaults to 0x12ED (more useful to modders)

* load bone pose script now works again with saved poses from older blends

* fixed numControlPoints attribute error when importing some kf files such as bowidle.kf (reported by Malo)

* Fallout 3 import (very experimental)

Version 2.3.12 (24 Oct 2008)
============================

* activated CivIV kf file export (uses Oblivion style kf, experimental!)

* added an option to disable material optimization (prevents "merging")

Version 2.3.11 (19 Oct 2008)
============================

* fix for fresh skeleton import into blends imported with the older script versions (again reported by periplaneta)

Version 2.3.10 (18 Oct 2008)
============================

* fix for skin exports from blends imported with older script versions reported by periplaneta)

Version 2.3.9 (12 Oct 2008)
===========================

* improved installer to point to Python 2.5.2 instead of Python 2.6 if Python installation is not found

* improved the test suite
  - allow comparison between imported and exported nif data
  - exported skinning data is now tested against imported skinning data

* added common base class for importer and exporter, for code sharing

* fixed bone correction application which would fail under certain circumstances

* epydoc documentation can now be generated and is included with the installation

Version 2.3.8 (27 Sep 2008)
===========================

* convert Bip01 L/R xxx to Bip01 xxx.L/R on import, and conversely on export (contributed by melianv, issue #2054493)

* fix for multi-material geometry morph (shape key) import and export

* show versions of scripts, Blender, and PyFFI, in import/export dialogue (issue #2112995)

* new export dialogue options to determine Oblivion weapon location as NiStringExtraData Prn value (issue #1966134)

Version 2.3.7 (25 Aug 2008)
===========================

* fixed export of cylinder radius on scaled objects

Version 2.3.6 (19 Aug 2008)
===========================

* added import of bhkNiTriStripsShape collisions

* fix for an exception when mixing mopps with other primitive shapes

* updated deprecated IPO and curve methods in keyframe export code

* improved FPS estimation on import

* check IPO curve completeness on export (solves the "NoneType has no evaluate attribute" problem)

* fixed scale keys import and export

Version 2.3.5 (25 Jul 2008)
===========================

* quick bug fix if you had multiple materials in your mopp

Version 2.3.4 (24 Jul 2008)
===========================

* fix for megami tensei imagine collision import

* on merge, do not skip keyframe controller block if the controller is not found in original nif file; instead, add a
  controller to the node in the nif file

* installer fixes for Vista and Blender 2.46

* updated for PyFFI 1.0.0, which includes the new mopp generator based on havok's recently released SDK

* removed mopp option from export config dialogue (they are now always generated)

* preserve the "skin", "dynalpha", ... material names

* fixed material merge bug

* fix for nif imports with more than 16 materials per mesh (the materials will not be merged in that case)

Version 2.3.3 (May 27, 2008)
============================

* updated installer to make sure PyFFI 0.10.9 is installed

Version 2.3.2 (May 27, 2008)
============================

* B-spline animations are now also imported

* new scripts to save and load current pose of bones to a text buffer this is useful when changing existing animations
  and starting/ending pose must be copied over from an existing animation)

* transform controller and interpolator also exported on the Bip01 node on Oblivion skeleton exports

* exporter no longer creates a NiTextKeyExtraData block on skeleton exports

Version 2.3.1 (Apr 13, 2008)
============================

* new script to set bone priorities on multiple bones at once

* Oblivion skeleton import and export including havok and constraints

* also import collision on scene root

* new settings in export dialogue to set material and extra havok presets for creature and weapon

* support for NiWireframeProperty via material WIRE mode

* furniture marker export

* prevent merging of EnvMap2 materials with other materials

* import of type 2 and 3 quaternion rotations

* import and export of BSBound bounding boxes for creatures

* many other minor enhancements

Version 2.3.0 (Mar 30, 2008)
============================

* Import/Export: experimental support for Oblivion animation
  - added keyframe file selection to import dialogue
  - kf file is merged with nif tree on import
  - includes text keys import from kf file
  - length 1 animations are exported as interpolators without further transform data, and interpolators without
    further transform data are imported as length 1 animations
  - bone priorities via NULL bone constraint name ("priority:xx")
  - fixed Euler rotation animation import (contributed by ahkmos)
  - bspline data is skipped on import
  - only tested on character animations (skeletonbeast.nif + any of the character/_male keyframe animations that
    don't contain bsplines)

* install.bat for quick windows installation

Version 2.2.11 (Mar 21, 2008)
=============================

* Export: NiVertexColorProperty and NiZBufferProperty blocks for Sid Meier's Railroads

Version 2.2.10 (Feb 26, 2008)
=============================

* Export: fix for a bug in reflection map export

Version 2.2.9 (Feb 22, 2008)
============================

* Import/Export: support for billboard nodes via TRACKTO constraint

* Import: re-enabled embedded texture support (they are saved to DDS)

Version 2.2.8 (Feb 11, 2008)
============================

* Export: more informative error messages if the mesh has no UV data and if the texture of type image has no image
  loaded

* Export: fixed NiGeomMorpherController target

Version 2.2.7 (Jan 11, 2008)
============================

* Export: fixed exception when mesh used material with vcol flags enabled but without any vertex colours present

* Import: strip "NonAccum" from the name when checking for node grouping

* Import: fixed misaligned collision boxes (sometimes you still have to switch to edit mode and back to align them
  correctly, seems to be a Blender bug)

Version 2.2.6 (Jan 8, 2008)
===========================

* Installer: fixed required PyFFI version

Version 2.2.5 (Dec 18, 2007)
============================

* Export: fixed bug in UV map export with smooth objects

Version 2.2.4 (Dec 10, 2007)
============================

* Import: fixed face orientation of imported bhkPackedNiTriStripsShapes

* Import: also import collisions of non-grouping NiNodes

Version 2.2.3 (Dec 8, 2007)
===========================

* Import/Export: added support for gloss textures (use MapTo.SPEC)

* Import/Export: added support for dark textures (use MapTo.COL and blendmode "darken")

* Import/Export: added support for detail textures (add a second base texture, that is, MapTo.COL)

* Import/Export: added support for multiple UV layers

* Import: removed broken pixel data decompression code, so recent nif versions with embedded textures can import (e.g.
  the copetech nifs)

Version 2.2.2 (Dec 2, 2007)
===========================

* Import/Export: support for Morrowind environment maps and bump mapping via NiTextureEffect blocks (set Blender Map
  Input to "Refl" for the NiTextureEffect texture, see release notes for more details)

* Import/Export: support for the bump map slot (Map To "Nor" in Blender)

* Import: fixed a bug which caused material duplication if materials were shared between more than one
  NiTriShape/NiTriStrips block

* Import: various small code improvements

Version 2.2.1 (Nov 27, 2007)
============================

* Import: havok blocks (still experimental, but seems to work on most nifs)

* Export: use bhkRigidBody instead of bhkRigidBodyT

* new tester for Blender import and export of havok related blocks

* fixed a bug in the uninstaller (it would not remove the weightsquash script)

Version 2.2.0 (Nov 19, 2007)
============================

* Export: new settings for Oblivion to control rigid body parameters and material

* Export: calculation of mass, center of gravity, and inertia tensor in rigid body, which is useful for non-static
  clutter

* Config: refactored the config GUI to get rid of most geometry parameters when drawing the GUI

* updated hull script for quickly creating approximate convex bounding shapes

* the hull script will only hull selected vertices when you run the script in edit mode

Version 2.1.20 (Nov 3, 2007)
============================

* Import/Export: updated for PyFFI 0.6

* Export: ignore lattices when checking for non-uniformly scaled objects

* Export: ignore name when avoiding duplicate material properties

* Test: added babelfish and Oblivion full body import/export tests

Version 2.1.19 (Oct 26, 2007)
=============================

* Import/Export: emulate apply mode via Blender's texture blending mode

Version 2.1.18 (Oct 25, 2007)
=============================

* Export: recycle material, alpha, specular, and texturing properties

Version 2.1.17 (Oct 23, 2007)
=============================

* Test: unselect objects when running each test (prevents duplicate exports)

* Import: new option to import bones with original nif matrices (useful in some cases where you do not want to bother
  with the correction matrices)

* Import: some minor optimizations and code cleanups

* Import: changed some lists to generators to save on memory

* Import: fixed trivial bug in get_blender_object

* Export: improved progress bar

* Export: warn when skin partition settings could be improved on Oblivion export

* Export: check Blender objects on non-uniform scaling before export so you do not need to wait too long before the
  scripts complain about it

Version 2.1.16 (Oct 21, 2007)
=============================

* Import: inform about the name of Blender object and nif block when losing vertex weights

* Import: update scene even if the import fails

* Import: fixed error with parentship if you imported a skeleton without selecting anything

* Import: new experimental option for importing meshes and parenting them to the selected armature (it seems to work
  pretty well for Oblivion meshes but not so good on Morrowind meshes)

* Import: improved Morrowind skeleton import (for example via base_anim files)

Version 2.1.15 (Oct 19, 2007)
=============================

* pycheck: added pychecker script (see http://pychecker.sourceforge.net/)

* test: added test script to automatically run importer and exporter on a range of selected nif and blend files

* Import/Export: PyFFI 0.5 is now required; the Blender scripts can now read and write a whole range of new nif
  versions (see PyFFI ChangeLog for details)

* Import/Export: small GUI improvements

* Import: ignore NiCamera root blocks instead of raising an exception on them

* Import: fixed a bug preventing animation import

* Import: fixed some progress bar issues

* Import: fixed bug in case of armature parents another armature (i.e. solstheim's ice minion raider), this is still
  not working perfectly but at least the import completes without raising exceptions

* Import: ``IMPORT_`` prefix for realigning option (in accordance with all other keys)

* Import: removed duplicate calculation of armature inverse matrix

* Import: replaced the deprecated method of linking armature to the scene

* Export: improved flatten skin so it works better in some cases

Version 2.1.14 (Oct 14, 2007)
=============================

* Import: fixed a transform bug which was introduced in 2.1.13, skinned geometries had their transform applied twice,
  so this fixes import of those skinned models that do not have a unit transform.

* Export: fixed a typo

* Import/Export/Config/GUI: restructured the scripts, in particular the import script has been transformed into an OOP
  class, so it requires no more globals for various settings. All gui and config related things have moved to a new
  nif_common.py library, as well as some common settings such as checking for Blender and PyFFI version. The result is
  that the code has been substantially simplified. The import and export script now also use exactly the same system to
  run the config gui.

Version 2.1.13 (Oct 13, 2007)
=============================

* Import: fixed transform error while joining geometries (this mostly affects the import of collision geometries)

* Import: optimized morph import yielding fewer array lookups and faster code

* Import: simplified texture searching and better Linux support by looking for lower case versions of names too

* Import: automatically remove duplicate vertices after joining Morrowind collision geometries

Version 2.1.12 (Oct 11, 2007)
=============================

* Import: provide sensible error message on kf import

* Export: set flags to 0x000E for Oblivion ninodes and nitrishapes/nitristrips

* Export: automatically set Blender collision type, draw type, and draw mode on old style (RootCollisionNode named
  mesh) Morrowind collision export

Version 2.1.11 (Oct 3, 2007)
============================

* Export: complain about unweighted vertices and select them, instead of adding an extra bone (this is a better
  alternative to the Scene Root.00 "feature" which was pretty frustrating at times when you had to hunt down unweighted
  vertices)

* Export: switched to using Mesh instead of using the deprecated NMesh

* Export: fixed frame time bug

* Import: removing dummy index does not properly delete the vertex from the mesh (yielding errors in the vertex key
  data), so reverted back to shift checking algorithm to fix face index order; the vertex order is shifted in place
  yielding simpler code and faster performance

* Import: removed _bindMatrix zombies, other minor cleanups

* Config: check Blender version and raise an exception if Blender is outdated

Version 2.1.10 (Sep 27, 2007)
=============================

* Export: fairly large restructuring of the code, the Python modules are only
  loaded once

* Export: fixed alpha controller export

* Export: removed disfunctional material color controller export

* Export: added a timer

* Export: new option to merge seams between objects, if you separated meshes in different parts then on export often
  seams could appear between the parts (the better bodies meshes are good examples of this problem), now there is an
  option to recalculate the normals on seams between objects on export (for better bodies the result is a seamless
  body on re-export)

Version 2.1.9 (Sep 21, 2007)
============================

* Export: new option to force dds extension of texture paths

* updated hull script for quickly creating bounding spheres

Version 2.1.8 (Sep 17, 2007)
============================

* Export: new padbones option which pads and sorts bones as required by Freedom Force vs. The 3rd Reich

* Export: automatic settings for Freedom Force vs. The 3rd Reich

* Export: compacter GUI

* new script for quickly creating bounding boxes 

Version 2.1.7 (Sep 9, 2007)
===========================

* Import: trishapes/tristrips of grouping NiNodes are merged on import and the resulting merged mesh is named after the
  grouping NiNode

* Import: 'Tri ' prefix is no longer removed from the name

* Import: simplified UV import and vertex color import code

* Import: fix for import of nifs with trishape/tristrip root

* Export: a simplified heuristic for naming blocks

* Export: raise exception if bone names are not unique

* Export: fixed exception when the bone name or armature name was very long

* Import/Export: support for Morrowind collision shapes using a polyhedron bounds shape

Version 2.1.6 (Sep 5, 2007)
===========================

* Import: Morrowind - better skeleton only import for better bodies

* Import: Morrowind - better import for better bodies

* Export: make 'Bip01' root node also the root of nif tree

Version 2.1.5 (Sep 2, 2007)
===========================

* Export: mopps for packed shapes

* Export: always strip texture paths (except for Morrowind and Oblivion)

* Import: shared texture folder detection for CivIV

* Import: assume stub has the alpha channel if the texture was not found and
  alpha property is present; this will ensure that NiAlphaProperty is written back on export

Version 2.1.4 (Aug 29, 2007)
============================

* Export: fixed more bugs in bhkConvexVerticesShape

* Export: NiVertexColorProperty and NiZBufferProperty blocks for CivIV

Version 2.1.3 (Aug 19, 2007)
============================

* Installer: also check in HKCU for registry keys of Python and PyFFI (fixes rare installation issue, see bug #1775859
  on the SF tracker)

* new script for reducing the number of influences per vertex, running this script before export helps if the skin
  partitioning algorithm complains about losing weights

Version 2.1.2 (Aug 17, 2007)
============================

* Installer: make sure user is admin ("fixes" the Vista bug)

* Import: parent selected objects to armature when importing skeleton only

* Import/Export: Python profiler support (read Defaults.py for details)

Version 2.1.1 (Aug 14, 2007)
============================

* Installer: open download page if dependency not found

* Export: make 'Scene Root' node scene root

* Export: quite a few bug fixes in Oblivion collision export, saner settings

* Export: option to toggle the use of bhkListShape

* Import: fix for skeleton.nif files

* Import: reverted to 2.0.5 bone import system if the bone alignment is turned off, looks much better for Oblivion
  imports

Version 2.1 (Aug 12, 2007)
==========================

* Export: added support for Oblivion collisions
  - bhkBoxShape (from Blender 'Box' bounding shape)
  - bhkSphereShape (from Blender 'Sphere' bounding shape)
  - bhkCapsuleShape (from Blender 'Cylinder' bounding shape)
  - bhkPackedNiTriStripsShape (from Blender 'Static TriangleMesh' bounding shape)
  - bhkConvexVerticesShape (from Blender 'Convex Hull Polytope' bounding shape); Note that many of the settings are
    not well understood, so you probably still have to tweak the collision settings in nifskope. But at least the
    collision geometries should be properly exported.

* Export: fixed another bind position transform bug (reported by Corvus)

* Export: fixed a few other minor bugs

Version 2.0.7 (Aug 8, 2007)
===========================

* Import: added support for multiple skeleton roots

* Import: better support for meshes/armatures parented to bones

* Import: added option to send bones to bind position

* Import: added option to control the application of skin deform

* Export: added option for stripification and strip stitching

* Export: fixed issue with non-uniform scaling on Freedom Force vs. 3rd Reich nifs

* Export: fixed issue with skin partition creation on older nif versions (such as Freedom Force vs. 3rd Reich nifs)

* Export: fixed problem with meshes sharing the same vcol lighting enabled material but not all having vertex weights
  (such as the Oblivion steel cuirass); the exporter now issues a warning rather than throwing an exception

* Export: fixed skin bounds calculation

Version 2.0.6 (Aug 6, 2007)
===========================

* Import/Export: fixed various transform errors

* Import: frames/sec detection

* Import: new and more reliable skinning import method

* Export: new options to control the export of skin partition

Version 2.0.5 (Jul 30, 2007)
============================

* Import: new option to import skeleton only

* Export: new options to export animation

* Export: 10.2.0.0-style transform controllers (includes Oblivion)

* Export: Morrowind style .kf files

* Export: fixed morph controller and morph data export

* Export: fixed getTransform on Zoo Tycoon 2 creatures

Version 2.0.4 (Jul 23, 2007)
============================

* Import: fixed a few skin import transform errors (Morrowind better bodies,
  Oblivion armour)

Version 2.0.3 (Jul 22, 2007)
============================

* Export: fixed skin export in case some bones did not influence any vertices

* Export: fixed transform error in skinned meshes such as better bodies and Oblivion skeleton

* Export: support for 20.3.0.3 and 20.3.0.6 (experimental)

Version 2.0.2 (Jul 16, 2007)
============================

* Import/Export: fix for config problem if nifscripts.cfg did not exist yet

Version 2.0.1 (Jul 14, 2007)
============================
* Import: fix in transform of some skinned meshes

* Import/Export: simple local install script in .zip for Linux

Version 2.0 (Jul 12, 2007)
==========================

* Import/Export: switched to PyFFI, support for NIF versions up to 20.1.0.3

* Import/Export: GUI revamped

* Export: tangent space calculation

* Export: skin partition calculation

* Export: skin data bounding sphere calculation

* Export: flattening skin hierarchy for Oblivion

Version 1.5.7 (Jul 13, 2006)
============================

* Import: further fix on zero length bones.

* Export: fixed export of unnamed objects.

* Export: fixed export of meshes parented to other meshes.

Version 1.5.6 (Jun 19, 2006)
============================

* Export: fixed export of multi-material meshes.

* Export: fixed export of zero-weighted vertexes.

Version 1.5.5 (Jun 15, 2006)
============================

* Import: fixed import of zero length bones.

* Export: fixed export of meshes with no parents. 

Version 1.5.4 (Jun 12, 2006)
============================

* Export: fixed a bug in apply_scale_tree

Version 1.5.3 (Jun 10, 2006)
============================

* Export: fixed an issue with skinned models (clothing slots now no longer require to be applied transformation with
  NifSkope)

* Import: fixed import of animation keys

* Export: no more empty NiNode at the end of bone chains

* Export: optimized the export of single material, non-animated meshes.

* Import/Export: bone names are restored

Version 1.5.2 (Apr 19, 2006)
============================

* Export: new option APPLY_SCALE (on by default) which resolves TESCS selection box issue and a 1.5 incompatibility
  problem

* Import/Export: full Python installation no longer needed

* Export: keyframe data realigned as well (should allow us, in theory, to re-export base animation files)

* Export: transform fix on dummy tail NiNodes

* Import: if texture not found, a stub is created

* Export: bone optimization fix

* Import: realignment is now always automatic

* Import/Export: correction on 1.5.1 ChangeLog, you'll still need the Bip01 spell, but we're getting closer

Version 1.5.1 (Apr 13, 2006)
============================

* Export: a 20.0.0.4 bug is fixed

* Import/Export: restoring bone matrices, no longer need for NifSkope's Bip01 spell

* Import: animated nodes that aren't bones have their animation imported too

* Import/Export: scaling fix

* Import: initial attempt to use the original NIF bone matrices if auto-align is turned off

Version 1.5 (Mar 21, 2006)
==========================

* Import: fix for models that have a NiTriShape as the root block

* Import: added config option to retain bone matrices

* Import: full animation support, animation groups and keyframes

* Import: detects invalid / unsupported NIF files

* Export: bugfix in animation export

* Export: bugfix in vertex weight export

* Export: large model fix (now supports up to 65535 faces/vertices per mesh

* Export: writes a dummy node on final bones to retain bone length when re-imported

Version 1.4 (Feb 12, 2006)
==========================

* Import: completely rewritten, uses Niflib now just like the exporter

* Import/Export: support for all NIF versions up to 20.0.0.4!!

* Import/Export: corrected specularity import/export (thanks NeOmega)

* Import/Export: hidden flag via object wire draw type

* Import: full skinning support (but still no animation)

* Import: better bone length estimation, automatic alignment

Version 1.3 (Jan 21, 2006)
==========================

* Import/Export: Vertex key animation support (geometry morphing).

* Export: Bugfix in bone animation export (transformations sometimes wouldn't show up correctly before).

* Import: Improved bone length calculation.

* Export: Added NIF v10.0.1.0 support.

* Export: Skinning bugfix for multi-material meshes.

* Export: Vertex weight calculation optimized, and no more annoying console messages!

* Export: Embedded textures reestablished.

Version 1.2 (Dec 23, 2005)
==========================

* Import/Export: updated for Blender 2.40

* Export: now uses Niflib, which implies that it runs much faster, the code is much cleaner, and multiple NIF version
  support is in the making

* Export: replaced old crappy config file system with Blender's native Script Config Editor system

* Export: new feature - texture flipping

* Export: new feature - export of bones, armatures, and vertex weights (finally!!!)

* Export: packed texture feature has been temporarily dropped; this functionality is being transferred to Niflib

Version 1.1 (Oct 31, 2005)
==========================

* Export: Fixed bug pointed out by Sabregirl, on mesh_mat_shininess.

* Export: Applied m4444x's patches to the exporter (texture flipping), changed names, included exporter readme file.

* Import/Export: Changed the licensing to BSD.

* Import: Added support for texturing in the editor 3D view. Now the textures will show up in textured mode if loaded.

* Import: NiMorph Controllers that m4444x coded. Haven't tested it, but it
  doesn't break the previous functionality, so it should be fine

* Export: Added an option for stripping the texture's file path

* Export: Support for subsurfed meshes (display level).

* Export: Vertex export method improved, extreme speedup!

* Import/Export: Transparency support improved.

* Import: Small fix in the import of vertex colours.

* Import: Autodetect Morrowind style texture path; if you load a NIF from ``..\meshes\..`` then the importer will look
  in ``..\textures\*`` for the NIF textures.

* Export: Fixed animation group export.

* Import: Multiple texture folders.

* Import/Export: number of vertices and number of faces is unsigned short: fix in importer, and added range check in
  the exporter.

* Import/Export: Added glow mapping.

* Export: Fixed texture flipping

* Import/Export: Config file support.

* Import/Export: Now we have a GUI for setting various options.

* Import: Solved problem with textures embedded in NIF file; textures will not load but the script will still load the
  meshes.

Version 1.0 (Oct 12, 2005)
==========================

* Initial bundled release of the importer v1.0.6 and exporter v0.8 on
  SourceForge.
