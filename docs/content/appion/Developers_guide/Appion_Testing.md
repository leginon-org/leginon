related issues: #671

There is a framework in place to write a test script for a particular data set that can be run on demand. The tests may be launched from the website and results of each executed command may be viewed from the web.

The following steps should be taken to add a new test.
 

1.  Select a session to be used as the test dataset. At AMI, test data set projects are named with the following format: zz_parttype_partname
    The test session names begin with "zz_". Currently, each test session may have only one test class associated with it.
    See issue #1229 for more information on AMI's test data sets.
     
2.  Add the session name to the $TEST_SESSIONS array located in config.php in the myamiweb directory.
     
3.  Make a copy of test_zz07jul25b.py located in myami/appion/bin and rename it to match your session name with "test_" prepended.
     
4.  Edit the new "test_zz....py" file.
    1.  Change the following class name at the beginning of the file to reflect your test session name:
             class Test_zz07jul25b(testScript.TestScript):

        
        This new class inherits all the properties and methods of the base class, TestScript, which is defined in myami/appion/appionlib/testScript.py. The TestScript class includes functions to create and execute commmands for many of the Appion programs like dogpicker, pyace, maxlikeAlign, uploadTemplate, etc.
    2.  At the bottom of the file replace the name of the class to be instantiated in the main function to match your new class name:
            if __name__ == "__main__":
                tester = Test_zz07jul25b()

        
        This main function will create an instance of your new class, run the start() function and finally run the close() function.
    3.  Modify the start() function of your new class to run the commands relevant to your data set. Review the functions available in testScript.py to decide which parameters need to be set for each function. If you need to execute a function that is not available in the TestScript class, you can add the function to the base class (TestScript) so that other test classes can use it, or, if the function is very specific to the data set that you are testing, you can add a new function directly to your new class. If you add a new type of program/command/function to the TestScript class, you will want to ensure that the report page path is included in the buildJobReportPageLink() function in myami/myamiweb/processing/testsuiterunreport.php.
         
5.  Run your test
    1.  Select your test session in the Appion Image Viewer and select Processing.
    2.  Scroll down to the bottom of the menu and select "Run Test Script"
    3.  Under "Limit: only process images" enter a small number between 1 and 10.
    4.  Select "just show command" and copy the resulting command to past into a terminal. See .... for more info on running from your sandbox.
    5.  Once the test has run, click on the # complete link under the Testing Tools section of the menu. Notice your test run information.
    6.  Select the test run to view a summary of the commands that were executed. Clicking on any of these will show more details of the run.
