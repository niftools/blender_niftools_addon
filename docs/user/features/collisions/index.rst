Collision Systems
=================
.. _collison-system:

The following section deals with the various collision systems that the Blender Niftools Addons supports.

.. toctree::
   :maxdepth: 1
   
   collision_objects
   collision_settings

.. _collison-workflow:

Workflow
--------

Here it is explained how to add collision to your mesh.

#. Go to :ref:`Collision Object <collisionobject>` and follow the steps
   indicated there:
   
   a) Choose between a :ref:`Bounding Box <collisionobject-bbox>` or :ref:`Havok Collision <collisionobject-havok>`.
   #) The bounding box is complete. If you have chosen Havok Collision proceed to choosing an 
      :ref:`appropriate shape <collisionobject-havokobject>` for your collision.
   #) Add a :ref:`Rigid Body <collisionobject-rigidbody>` modifier.
       
#. Go to :ref:`Collision Settings <collisonsettings>` and follow the steps indicated there:

   a) Start by :ref:`enabling collision bounds <collisonsettings-enable>`.
   #) Define the the :ref:`Havok Settings <collisonsettings-havok>` for your
      collision bounds.
   
.. Add a :ref:`Collision <collisionobject-collmodifier>` modifier. Not sure
.. if needed/used check its own section.
   