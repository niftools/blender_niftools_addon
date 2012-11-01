Workflow
========

Install
-------

To install the plugin from a git checkout,
run the following in a buildenv (Windows)::

  install.bat

or from a terminal (Linux)::

  sh install.sh

from within the ``blender_nif_plugin/install`` folder.

Run Regression Tests
--------------------

To run all tests, run the following in a buildenv (Windows)::

  blender-nosetests.bat

or from a terminal (Linux)::

  sh blender-nosetests.sh

from within the ``blender_nif_plugin/test`` folder.
This will test the currently installed plugin
(*not* your checked out version!)
so usually you would install it first.

Beware that the output can be rather verbose,
so you may have to scroll quite a bit to see the relevant backtrace.

Each test resides as a python file in the ``blender_nif_plugin/test/test`` folder.
To run a particular test only, specify the file as an argument; for instance::

  blender-nosetests.bat test/test_cube.py

Actually, all command line arguments of ``nosetests`` apply.
For more details, run::

  blender-nosetests.bat --help

Also see the
`nose manual <http://readthedocs.org/docs/nose/en/latest/usage.html#options>`_.

Generate Documentation
----------------------

Run the following in a buildenv (Windows) or terminal (Fedora)::

  make html

from within the ``blender_nif_plugin/docs`` folder.

To view the docs, open ``docs/_build/html/index.html``.
