Continuous Integration Build Server
===================================

.. _development-testframework-ci_server:

The following section is both for internal reference for the build server used by the Niftools team.
We encourage developers to build their own; it provides a fast feedback loop, encourages you to run a test and fix them when they get broken. 
We use Jenkins as our build server

Installed Plug-ins

 - Git Client & Git Plugins: Used to grab the repo
 - Hudson Build-publisher Plugin: Pre-installed 
 - Jenkins Cobertura Plugin: Used to publish coverage reports
 
Optional Plug-ins
 - IRC Plugin: IRC bot which allows you trigger builds remotely

Project Name ::
	
	blender_niftools_addon

Git Repository ::
	
	git://github.com/niftools/blender_niftools_addon.git

Branches ::
	
	develop

Build Triggers ::
	
	Poll SCM
	Build Periodically

Inject Environment variables ::
	
	..<path_to_jenkins>/.jenkins/workspace/bin/blender.properties

Build Steps
***********

Build ::

	> cd install
	> DEL *.zip
	> makezip.bat
	
Unit Test ::

	> cd testframework
	> blender-nosetests.bat 
	--with-xunit 
	--xunit-file=reports\unit.xml 
	--cover-xml 
	--cover-package=io_scene_niftools unit
	
Integration Test ::

	> cd testframework
	> testframework\blender-nosetests.bat 
	--with-xunit 
	--xunit-file=testframework\reports\integration_test.xml 
	--cover-package=io_scene_niftools
	--cover-xml-file=testframework\reports\integration_test_coverage.xml 
	testframework\integration
	
Nightly ::

	> cd install
	> ren *.zip blender_niftools_addon_%BUILD_NUMBER%_%BUILD_ID%.zip
	> xcopy /K /F  "*.zip" "%build_folder%\blender_niftools_addon\nightly\"
	

	

Post Build Actions
******************

Publish Cobertura Coverage reports ::

	testframework/reports/*.xml
	
Publish XUnit test reports ::

	testframework/reports/*.xml