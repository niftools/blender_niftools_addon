Contributions Overview
======================

The project is always looking for people to contribute to the project. The following rules are guidelines for the various forms of contributions. 

Code Contribution Process
-------------------------

Contributions should always be made through GitHub's Pull Request (PR) feature, branched from latest `develop` branch.
This repo comes with a template for Pull Requests and should be fully completed.

Once the PR is submitted, the @niftools/blender-nif-plugin-review team is automatically notified and will start a discussion process.
This can include ensuring the commit is beneficial to the project as a whole, is appropriately scoped, discuss any issues with the design, ensure all requirements are met. 
This is an iterative process; additional commits can be appended at any time based on PR discussion to the source branch and will be automatically included in the PR.

There are three conditions any contribution to the codebase should respect:
 - Clean, commented implementation that doesn't break existing functionality
 - Tests to prove the implementation works and regression is still green
 - Appropriate documentation updates

These are not exclusive conditions for a contribution to be accepted, but generally enforced as close as possible to ensure quality.
Merging of the PR is at the discression of the @niftools/blender-nif-plugin-merge team.

Code
~~~~

General rule of thumb is to see what has gone before, but if your way is better, ensure you demonstrate that to the review team. 
 * Adhere to conventions, see out main documenation for developers.
 * Code should be as readible as possible.
 * Comments should help break down complex behavior. If the behavior is too complex, group the code into logical chuncks, or extract to functions for easier to understand code.
 * Docstrings - Ensure that the intention, not the implementation is described. Self describing code is good, but if it doesn't do as intended, the s what is coded may work, but not be what 

Testing
~~~~~~~

Our template includes sections relating to ensure appropiate testing has been completed.
 * If you change the behavior of part of the code, you should try to change the relevant tests to adapt to the new behavior.
 * If a test fails, it has to be fixed either in the test or the code.

When possible, for evey API additions add either unit or integration tests.
The template requires documenting any tests changes in the Pull Request, and be prepared to answer questions about test changed or deletion.

Documentation
~~~~~~~~~~~~~

Documentation is used by both users and developers and is published.
 * Any updates that add, remove or modify behaviour require corresponding updates to ensure that user can use the functionality
 * Supporting developer documentation should be updated with relavent changes, design decisions, etc. 

Reviewer Contribution
---------------------

The reivew group is to ensure that contributions are openly discussed, people can participate in the development process and ensure quality of development
 * If you are interested in joining the review group to give your input on contributions, talk to the @niftools/core team to be added as reviewer.
 * You will automatically recieve notificiations for any PR related to this repo.

Release process
---------------

When all issues in a milestone are complete, a release branch is created from the `dev` branch, tagged, log updates and PR done towards `master`.  
 * The project uses the python versioning scheme - https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
 * A release will always include an accompaning version change, but the reverse is not true : the version can change without a release.
After being merged, a release will be officially released using the GitHub release system.



