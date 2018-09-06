Interactive Development Environment
===================================

.. _development-design-setup-ide:

`PyCharm <https://www.jetbrains.com/pycharm/>`_ IDE is the preferred way to allows us maintain a unified workflow for general file manipulation,
repo management, python scripting, and hooks into Blender's debugging server.


Install PyCharm
---------------

**Windows**

#. Download `PyCharm <https://www.jetbrains.com/pycharm/download>`_

**Fedora**, simply run::

   sudo yum install eclipse eclipse-egit eclipse-pydev

**Ubuntu**, simply run::

   sudo snap install [pycharm-professional|pycharm-community] --classic

When starting pycharm, Open the workspace folder.
If you followed the instructions, you should have cloned the code into ``/home/<username>/workspace`` PyCharm will automatically recognise this as a Git repo.

Debugging
-----------------

The Blender Nif plugin code comes with built-in pydev hook to allow connection by a Remote Python Debug Server.
This allows run-time debugging; watching the script execute, evaluate variables, function call stack etc.

Debugger
````````````````````````````
    ..TODO


Happy coding & debugging.
