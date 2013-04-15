Workflow
========

The aim of this section is to describe the desired workflow for a developer

.. _development-porting_strategy:

Porting Strategy
----------------

We are following the following strategy for porting the plugin:

#. Write regression test for desired feature.
#. Run the test.
#. Fix the first exception that occurs, and commit the fix.
#. Go back to step 2 until no more exceptions are raised.
#. Do the next 2.6.x release.
#. Listen to feedback from users, and go back to step 1.

The 2.6.x series is designated as purely experimental.

Once enough features have and pass their regression test---i.e. as
soon as the new plugin can be considered en par with the old
scripts---the code will be refactored and cleaned up, possibly moving
some bits out to seperate addons (hull script, morph copy, etc.). The
refactor is reserved for the 3.x.x series.

Generate Documentation
----------------------

Run the following in a buildenv (Windows) or terminal (Fedora)::

  make html

from within the ``blender_nif_plugin/docs`` folder.
The generated API documentation
will correspond to the currently installed plugin
(*not* your checked out version!)
so usually you would install it first.

To view the docs, open ``docs/_build/html/index.html``.
