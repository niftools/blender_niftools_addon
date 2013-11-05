

Project Name : blender_nif_plugin

Git Repository : git://github.com/niftools/blender_nif_plugin.git
Branches : develop

Build Triggers


Inject Environment variables : <path_to_jenkins>/.jenkins/workspace/bin/blender.properties

Build Steps :

	Build
	cd install
	DEL *.zip
	makezip.bat
	
	cd install
	ren *.zip blender_nif_plugin_%BUILD_NUMBER%_%BUILD_ID%.zip
	xcopy /K /F  "*.zip" "%build_folder%\blender_nif_plugin\nightly\"
	
	cd testframework
	blender-nosetests.bat --with-xunit --xunit-file=reports\unit.xml 
	--cover-xml --cover-package=io_scene_nif unit
	
	cd testframework
	testframework\blender-nosetests.bat --with-xunit --xunit-file=testframework\reports\integration_test.xml 
	--cover-package=io_scene_nif --cover-xml-file=testframework\reports\integration_test_coverage.xml testframework\integration
	

Post Build Actions : 

	Publish Cobertura Coverage reports
	testframework/reports/*.xml
	
	Publish XUnit test reports
	testframework/reports/*.xml