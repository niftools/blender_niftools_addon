
.. _collison-system:

Collision Systems
-----------------

The follow section deals with the various collision systems that the Blender Nif Plugins supports.

.. toctree::
   :maxdepth: 1
   
   collision_objects
   collision_settings

.. _collison-worflow:

Worflow
=======

Here it is explained how to add collision to your mesh.

#. Go to :ref:`Collision Object <collisionobject>` and follow the steps indicated there:
   
   a) Choose between a :ref:`Bounding Box <collisionobject-bbox>` or :ref:`Havok Collision <collisionobject-havok>`.
   #) The bounding box is complete. If you have chosen Havok Collision proceed to choosing an :ref:`appropriate shape <collisionobject-havokobject>` for your collision. 
   #) Add a :ref:`Rigid Body <collisionobject-rigidbody>` modifier.
   
.. Add a :ref:`Collision <collisionobject-collmodifier>` modifier. Not sure if needed/used check its own section.
   
   
#. Go to :ref:`Collision Settings <collisonsettings>` and follow the steps indicated there:

   a) Start by :ref:`enabling collision bounds <collisonsettings-enable>`.
   #) Define the the :ref:`Havok Settings <collisonsettings-havok>` for your collision bounds.
   
   