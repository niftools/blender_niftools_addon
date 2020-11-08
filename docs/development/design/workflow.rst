========
Workflow
========

.. _development-design-workflow:

The aim of this section is to describe the desired workflow for a developer

----------------
Porting Strategy
----------------

We are following the following strategy for porting the addon:

#. Write a regression test for the desired feature.
#. Run the test.
#. Fix the first exception that occurs, and commit the fix.
#. Go back to step 2 until no more exceptions are raised.
#. Do the next release.
#. Listen to feedback from users, and go back to step 1.

The 0.x series is designated as purely experimental.

Once enough features have and pass their regression test---i.e. as soon as the new addon can be considered on par
with the old scripts---the code will be refactored and cleaned up, possibly moving some bits out to separate addons
(hull script, morph copy, etc.). The refactor is reserved for the 1.x.x series.

----------------------
Generate Documentation
----------------------

Run the following in a buildenv (Windows) or terminal (Fedora)

.. code-block:: shell

  make html

from within the ``blender_niftools_addon/docs`` folder. The generated API documentation will correspond to the
currently installed addon (*not* your checked out version!) so usually you would install it first.

To view the docs, open ``docs/_build/html/index.html`` in a web browser of your choice.
