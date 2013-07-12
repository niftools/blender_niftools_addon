Development Methodology
=======================

A Methodology is guideline for the principles we want for development process.

For the 2.6.x series of development we decided to develop a Feature Oriented, Test Driven Development (TDD) methodology to suit both current and future needs.

Test driven development in a nutshell means:
 * We write a test for some functionality we want.
 * We run the test, initially it will fail.
 * We code the feature.
 * We re-run our tests, changing the code until it passes.
 
The advantages of TDD is:
 * It gives us quick feedback when changes arises.
 * Constantly testing the code to ensure that it is doing what is meant to do, no assumptions.
 * When things break, it narrows the search; allowing fixes to be developed more quickily.
 * Ensure that the changes haven't broken any other existing funcitonality.

**The focus of our TDD methodology is 3 main areas:**

 * Develop maintainable code
 * Testing features 
 * Documentation 
 
Code Development & Maintenance
------------------------------

The initial proposal was to port all the current code directly to the new Blender Python API.
See :ref:`Code Porting Strategy <development-porting_strategy>`

Additionally::

   * It was decided that as code was ported that the conventions as described in the next section
   would be introduced to keep the code consistent and improve readability.

   * Refactored of code into modular components when working on features sets; collisions, texture, armature etc. 

Naming Conventions
******************

* Stick to the official Python style guide (`PEP 8
  <http://www.python.org/dev/peps/pep-0008/>`_).
  
* Instances of blender classes start with ``b_`` whilst instances of
  nif classes start with ``n_``. Examples:

  * ``b_mesh`` for a blender :class:`bpy.types.Mesh`
  * ``b_face`` for a blender :class:`bpy.types.MeshFace`
  * ``b_vertex`` for a blender :class:`bpy.types.MeshVertex`
  * ``b_vector`` for a blender :class:`mathutils.Vector`
  * ``b_obj`` for a blender :class:`bpy.types.Object`
  * ``b_mat`` for a blender :class:`bpy.types.Material`
  * ``b_bone`` for a blender :class:`bpy.types.Bone`
  * ``n_obj`` for a generic :class:`pyffi.formats.nif.NifFormat.NiObject`
  * ``n_geom`` for a :class:`pyffi.formats.nif.NifFormat.NiGeometry`

.. todo::

   These conventions are not yet consistently applied in the
   code. Stick to it for new code, but we are holding off a rename for
   the planned 3.x.x refactor.
   
Modularisation
**************

During the code porting process it became apparent that the code was monolithic. All of the import code was in one class, all export code in another.
Initially we planned to hold off large scale refactoring until the code was ported and do it as part of the 3.0.x series.
It was decided to seperate out common areas of functionatlity into submodules which would be responsible for that specific areas.

 * Some systems are still highly coupled, such as geometry generation with the material system, these will remain in place.

Modularisation of code makes it much easier to add on new functionality, such as new collision type, when the code is localised
This will also make the refactoring process easier as we can target specific areas.

Git Development Model
---------------------

We use git as our version control system. In order to facilitate parallel development of a single code base, 
we developed a git workflow based on the popular nvie gitflow model.

The goals were:
 
 #. Central clean repository which everyone forks from, avoids new developer cleaning up unwanted branches
 #. Developers create feature branch off develop, rebase if develop is updated
 #. Central repository to accept pull requests, for peer review.
 #. Merge code into develop, developers synch with central
 
When a develop forks from the central repo, their repo will have only 2 branches, master & develop.

 * Their primary use is tracking updates from central; only changes should be those pulled from the central repo.
 * Develop is used as the base to create feature branches.
 * If develop is updated, then all feature branches should be rebased. This reduces conflicts for pull requests sent to the central repo. 

  :image: http://i211.photobucket.com/albums/bb189/NifTools/Blender/documentation/Git%20Development%20Model/git_developer_model_zps55d02850.png

When a developer feels that their feature branch is ready they can start the review process

 * A pull request needs to be sent to the central repo against the develop branch.
 * A review for that specific project will review the pull request
 * If they are happy with the changes it will be merged into develop and all active developers will be notified to pull the changes into their local repos.
 * If additional changes are required then the pull request if left open and the developer can add commits to their repo which get automatically added to the pull request. 
 
 :image: http://i211.photobucket.com/albums/bb189/NifTools/Blender/documentation/Git%20Development%20Model/git_developer_model_zps55d02850.png
 
Test-Framework
**************

In Test Driven Development, tests are the core to ensuring software quality. 
Before any production code is writen, a test should be written to check to see that the code does what it does. 
Initially the tests will fail. As the code is developed, then more tests should pass until all tests do. 
At this point a feature is deemed to be implemented.

Some points of note:

 * It is up to the developer to create tests which are appropriate in the level of testing.

Previous, tests were created ad-hoc, based often on bug fixes, so did not extensively test the code.
It was decided that we would develop a test-framework to standardise testing in parallel to the porting process.
The current goal of the test-framework is to provide integration level testing to ensure features function as required.

The Test Framework has several purposes 

 * Standardise testing through the use of the template pattern.
 * Provide functionality testing as features are ported to the newer api.
 * Act as a regression suite so that future changes to the api will be detected.
 * Provide a list of supported plugin features by testing features and asserting that they are known to be working.
 * Provide documentation of features by recreating user interaction.

Feature Tests Creation
----------------------

Supporting features is detailed workflow is detail in the :ref:`Test Framework Section <development-porting_strategy>`.

Documentation
-------------

Documentation forms the final core principle of development. Unless the users can understand how to use the plugin, there is 
not much point in development. 

   