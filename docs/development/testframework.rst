Test Framework
==============

.. _developer-testframework:


The test framework is 

Install
-------

To install the plugin from a git checkout,
run the following in a buildenv (Windows)::
   
   cd blender_nif_plugin/install
   install.bat

or from a terminal (Linux | Ubuntu)::
   
   ./blender_nif_plugin/install
   sh ./install.sh
   

Tests
-----

Ideally, for every feature, first, a regression test should be
written.

The following process is followed:

#. Create a new python file to contain the feature regression test
   code. For example, if the feature concerns *x_feature*, the test case
   would be stored in ``testframework/test/../../test_x_feature.py``.
   Derive the test class from
   :class:`test.SingleNif`, and name it :class:`TestBlabla`.

   .. Note::
      Use the template available in ``testframework/test/template.py``.

Each test should overwrite the following methods from :class:`test.SingleNif`

   * The :meth:`n_create_data` used to create the physical .nif
   * The :meth:`n_check_data` used to test the data of physical .nif
   * The :meth:`b_create_objects` used to mimic how the user would create the objects. 
   * The :meth:`b_check_data` check blender data, used to check before export and after import.
   
   Where possible reuse methods from other tests to build up the tests in blocks 
   and make it reusable for the specific code to the features.

#. Write feature test data and test code on nif level:

 - Create a nif (say in nifskope, or with the old blender nifscripts).
   Take care to make the file as simple as possible.

 - Use pyffi's ``dump_python`` spell to convert it to python code.
  
 - Store the relevant parts of the code in ``testframework/test/../../n_gen_x_feature.py``.
   The :meth:`n_create_data` method of the test class will call the methods from :mod:`n_gen_x_feature` module
   to construct the nif data.

    .. Note::
       
       We move all the code to external modules for code reuse code as importing other tests will cause those tests to be re-run unnecessarily.

 - Write Python code which test the nif against the desired feature.
   This code goes in the :meth:`n_check_data` method of the test class.

#. Write feature test code on blender level:

  - Write Python code which create the corresponding blender scene in ``testframework/test/../../b_gen_x_feature``.
    
  - Where possible make the test case as simple as possible. For
    instance, use primitives readily available in blender. This code
    goes in the :meth:`b_create_objects` method of the test class.

  - Document the feature in ``docs/features/x_feature.rst`` as you write
    :meth:`b_create_objects`: explain what the user has to do in blender in order
    to export the desired data, and where in blender the data ends up
    on import.

  - Write Python code which test the blender scene against the
    desired feature: :meth:`b_check_data` method of the test class.

#. Now implement the feature in the import and export plugin, until
   the regression test passes.

That's it!

#. Create a new text file ``docs/features/blabla.rst`` to contain the
   feature user documentation,
   and add it to the table of contents in ``docs/features/index.rst``.
   If there are particular issues with the feature's implementation, 
   make a note of it in ``docs/development/design.rst``.

The tests will actually do the following:
  
   * Python generated part
  
   #. Starts by :meth:`n_create_data` creating physical nif ``test/nif/../../x_feature_py_code.nif``.
    
   #. :meth:`n_check_data` is called to ensure nif is correct.

   #. Nif is imported into blender, the scene is saved to ``test/autoblend/../../x_feature_pycode_import.blend``
   
   #. :meth:`b_check_data` is called on imported scene.

   #. Nif is exported to ``test/nif/../../x_feature_export_pycode.nif``
   
   #. :meth:`n_check_data` on exported nif.
   
   * User generated part
   
   #. :meth:`b_create_objects` to create the scene, saved to ``test/autoblend/../../x_feature_userver.blend``
   
   #. :meth:`b_check_data` to check it before export

   #. Export the nif to ```test/nif/../../x_feature_export_pycode.nif``
   
   #. :meth:`n_check_data` to check exported nif.

   #. import the exported nif, saved to ``test/autoblend/../../x_feature_userver_reimport.blend``
   
   #. :meth:`b_check_data` tests the imported scene.

This ensures data integrity both at Blender level and at nif level.

.. generate, and link to, test API documentation?


Run Regression Tests
--------------------

To run all tests, run the following in a buildenv (Windows)::

  blender-nosetests.bat

or from a terminal (Linux | Ubuntu)::

  sh ./blender-nosetests.sh

from within the ``blender_nif_plugin/testframework/`` folder.

Each test resides as a python file in the ``blender_nif_plugin/testframework/test/`` folder.
To run a particular test only, specify the file as an argument; for instance::

  blender-nosetests.bat test/geometry/trishape/test_geometry.py

Actually, all command line arguments of ``nosetests`` apply.
For example, to abort on first failure::

  blender-nosetests.bat -x

For more details, run::

  blender-nosetests.bat --help

* The tests will run on the currently installed plugin (*not* your checked out version!) so usually ensure you re-install after making edits to add-on files.
* Beware that the output can be rather verbose, so you may have to scroll quite a bit to see the relevant backtrace.

Also see the
`nose manual <http://readthedocs.org/docs/nose/en/latest/usage.html#options>`_.
