*************
Documentation
*************
.. _developement-docs:

Documentation of the Blender Niftools Addon is of equal importance to having a clean, functional code base and automated tests.
The addon is intended to be used by content creators. The main causes for inability to use it correctly are.
- Functional bugs
- Design and usability issues
- Poorly documented features.

The first two issues can be fixed on a priority basis unless things are documented to reflect there are known issues or the workflow is outlined correctly
users will be able to use the addon correctly. This results in poor user experience and more work for developers as they will have to respond to support requests.

==========
Convention
==========
.. _developement-docs-convention:

This chapter outlines the convention for documentation based on the `Python style guide <https://docs.python.org/devguide/documenting.html#style-guide>`_

| Section headers are created by underlining (and optionally overlining) the section title with a punctuation character, at least as long as the text:
| 
| =================
| This is a heading
| =================
| Normally, there are no heading levels assigned to certain characters as the structure is determined from the succession of headings. However, for the Python documentation, here is a suggested convention:
|
| # with overline, for parts
| * with overline, for chapters
| =, for sections
| -, for subsections
| ^, for subsubsections
| ", for paragraphs