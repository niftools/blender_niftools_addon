Workflow
========

Import Project Into Eclipse
---------------------------

1. Go to: **File > Import > General > Existing Projects into Workspace > Next > Browse**.

2. Choose the ``blender_nif_scripts`` folder and select **Ok > Finish**.

3. If you want to use git from within eclipse, right click the project
   in the Project Explorer, and choose **Team > Share Project > Git**.
   Enable **Use or create Repository in parent folder of project**,
   and click **Finish**.

Run Regression Tests
--------------------

Run the following in a buildenv (Windows)::

  blender-nosetests.bat

or terminal (Fedora)::

  ./blender-nosetests.sh

from within the ``blender_nif_scripts`` folder.

Generate Documentation
----------------------

Run the following in a buildenv (Windows) or terminal (Fedora)::

  cd blender_nif_scripts/docs
  make html

To view the docs, open ``docs/_build/html/index.html``.
