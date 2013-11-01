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
   

Test Template
-------------

For every feature, first, a test should be written.

The following process is followed:

#. Create a new python file to contain the feature test code. 
   For example, if the feature concerns *x_feature*, the test case
   would be stored in ``testframework/test/../../test_x_feature.py``.
   
#. Derive the test class from :class:`test.SingleNif` and name it :class:`TestXFeature`.
   :class:`test.SingleNif` is a designed upon the template pattern and takes care of all execution, loading of files and clean up.
   
   .. Note::
      A template for a test class is available in ``testframework/test/template.py``.

#. Each test needs to overwrite the following methods from :class:`test.SingleNif`

   * The :meth:`n_create_data` used to create the physical .nif
   * The :meth:`n_check_data` used to test the data of physical .nif
   * The :meth:`b_create_data` used to mimic how the user would create the objects. 
   * The :meth:`b_check_data` check blender data, used to check before export and after import.
   
These methods are intended to be delegate function, calling external methods in either n_gen_xxxx or b_gen_xxxx files.
   
   * We move all the code to external modules for code reuse code to avoid importing other tests, avoiding tests to be re-run unnecessarily.
       

Test Implementation
-------------------
   
Each test has two paths of execution one importing/export a python generated nif, 
the other exporting/importing a nif created by mimmicking how a user would create it.
Each test can be comprised of multiple required features and a lego block-building 
approach should be taken to building the nifs.

#. Recreate the nif using python:

  - Create a nif (say in nifskope, or with the old blender nifscripts).
    Take care to make the file as simple as possible.

  - Use pyffi's ``dump_python`` spell to convert it to python code.
  
  - The :meth:`n_create_data` method of the class will call the methods 
    from :mod:`n_gen_x_feature` module to construct the physical nif.
    It may be required to call other reusable functions from other tests.
    Reusable functions should be created from the dump_python and stored in ``testframework/test/../../n_gen_x_feature.py``.

 - Write code to test the desired features of the physical.
   The :meth:`n_check_data` method will call the methods 
   from :mod:`n_gen_x_feature` module to check the nif data.

#. Recreate the feature within blender, using user functions:

  - Write Python code which recreates the corresponding data in the blender scene in ``testframework/test/../../b_gen_x_feature``.
    
  - Where possible make the test case as simple as possible. For
    instance, use primitives readily available in blender. This code
    goes in the :meth:`b_create_data` method of the test class.

  - Document the feature in ``docs/features/x_feature.rst`` as you write
    :meth:`b_create_data`: explain what the user has to do in blender in order
    to export the desired data, and where in blender the data ends up
    on import.

  - Write Python code which test the blender scene against the
    desired feature: :meth:`b_check_data` method of the test class.

#. Now implement the feature in the import and export plugin, until
   the regression test passes.

That's it!

Execution Order
---------------

The tests will run like this:
  
 * Python generated part
  
   #. Starts by :meth:`n_create_data` creating a physical nif ``test/nif/../../x_feature_py_code.nif``.
    
   #. :meth:`n_check_data` is called to ensure nif is correct before importing.

   #. Nif is imported into blender, the scene is saved to ``test/autoblend/../../x_feature_pycode_import.blend``
   
   #. :meth:`b_check_data` is called on imported scene to verify scene data.

   #. Nif is exported to ``test/nif/../../x_feature_export_pycode.nif``
   
   #. :meth:`n_check_data` on exported nif to verify nif data.
   
 * User generated part
   
   #. :meth:`b_create_data` to create the scene, saved to ``test/autoblend/../../x_feature_userver.blend``
   
   #. :meth:`b_check_data` to check it before export

   #. Export the nif to ```test/nif/../../x_feature_export_pycode.nif``
   
   #. :meth:`n_check_data` to check exported nif.

   #. import the exported nif, saved to ``test/autoblend/../../x_feature_userver_reimport.blend``
   
   #. :meth:`b_check_data` tests the imported scene.

This ensures data integrity both at Blender level and at nif level.

.. generate, and link to, test API documentation?


Documentation
-------------

 * Create a new text file ``docs/features/../../feature_x.rst`` to contain the feature user documentation. 
 
 * Add it to the table of contents in ``docs/features/index.rst``.
 
 * If there are particular issues with the feature's implementation, make a note of it in ``docs/development/design.rst``.

Running Tests
-------------

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
