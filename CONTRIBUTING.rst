Contributions Overview
======================

The project is always looking for people to contribute to the project. The following rules are guidelines for the various forms of contributions. 

Code Contribution Process
-------------------------

Contributions should always be made through GitHub's Pull Request (PR) feature, branched from latest `develop` branch.
This repo comes with a template for Pull Requests and should be fully completed.

Once the PR is submitted, the @niftools/blender-niftools-addon-review team is automatically notified and will start a discussion process.
This can include ensuring the commit is beneficial to the project as a whole, is appropriately scoped, discuss any issues regarding the design, and ensuring all requirements are met. 
This is an iterative process; additional commits can be appended at any time based on PR discussion to the source branch and will be automatically included in the PR.

There are three conditions any contribution to the codebase should respect:
 - Clean, commented implementation that doesn't break existing functionality
 - Tests to prove the implementation works and regression is still green
 - Appropriate documentation updates

Merging of the PR is at the discretion of the @niftools/blender-niftools-addon-merge team.
These are not exclusive conditions for a contribution to be accepted but generally enforced as close as possible to ensure quality.

Code
~~~~

The general rule of thumb is to see what has gone before, but if your way is better, ensure you demonstrate that to the review team. 
 * Adhere to conventions, read main documentation for developers.
 * Code should be as easy to read as possible.
 * Comments should help break down complex behaviour. If the behaviour is too complex, group the code into logical chunks, or extract to functions to make it easier to understand the code.
 * Docstrings to describe the intention, not implementation. Self-describing code is good and may provide functionality, but useless if it doesn't do what is actually needed.

Testing
~~~~~~~

Our template includes sections relating to ensure appropriate testing has been completed.
 * If you change the behaviour of part of the code, you should try to change the relevant tests to adapt to the new behaviour.
 * If a test fails, it has to be fixed either in the test or the code.

When possible, for every API additions add either unit or integration tests.
The template requires documenting any tests changes in the Pull Request. Expect questions about any test updates or deletions.

Documentation
~~~~~~~~~~~~~

Documentation is used by both users and developers and is published.
 * Any updates that add, remove or modify behaviour require corresponding updates to ensure that user can use the functionality
 * Supporting developer documentation should be updated with relevant changes, design decisions, etc. 

Reviewer Contribution
---------------------

The review group is to ensure that contributions are openly discussed, people can participate in the development process and ensure the quality of development
 * If you are interested in joining the review group to give your input on contributions, talk to the @niftools/core team to be added as a reviewer.
 * You will automatically receive notifications for any PR related to this repo.

Release process
---------------

When all issues in a milestone are complete, a release branch is created from the `dev` branch, tagged, log updates and PR done towards `master`.  
 * The project uses the Python versioning scheme - https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
 * A release will always include an accompanying version change, but the reverse is not true: the version can change without a release.
After being merged, a release will be officially released using the GitHub release system.



