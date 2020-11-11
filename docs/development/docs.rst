*************
Documentation
*************
.. _developement-docs:

Documentation of the Blender Niftools Addon is of equal importance to having a clean, functional code base and
automated tests.

The addon is intended to be used by content creators. The main causes for inability to use it correctly are:
- Functional bugs
- Design and usability issues
- Poorly documented features.

The first two issues can be fixed on a priority basis, unless the issue is caused by the user not reading documented
known issues or workflow steps.

Good documention helps reduce user friction and helps keep developers from responding to support questions.

Convention
==========
.. _developement-docs-convention:

This chapter outlines the convention for documentation based on the `Python style guide
<https://docs.python.org/devguide/documenting.html#style-guide>`_.

Section headers are created by underlining (and optionally overlining) the section title with a punctuation
character, at least as long as the text.

Normally, there are no heading levels assigned to certain characters as the structure is determined from the
succession of headings. We use the following conventions, based on the Python documentation:

| **#** with overline, for parts

.. code-block:: text

  #######################
  This is a document part
  #######################

| **\*** with overline, for chapters

.. code-block:: text

  *****************  
  This is a chapter  
  *****************

| **=**, for sections

.. code-block:: text

  This is a chapter section  
  =========================  

| **-**, for subsections

.. code-block:: text

  This is a chapter sub-section  
  -----------------------------  

| **^**, for subsubsections

.. code-block:: text

  This is a chapter sub-sub-section  
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  