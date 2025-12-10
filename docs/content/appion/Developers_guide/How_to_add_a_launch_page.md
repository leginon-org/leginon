If you are adding a GUI to launch a python script that is based on the AppionLoop class found in appionLoop2.py, follow the [directions for adding an AppionLoop GUI page](/appion/directions_for_adding_an_AppionLoop_GUI_page).

1.  **Add a php page with the basic appion template**
     
    Most of our launch pages are php files with at leat 2 functions, one to create a form for the user to fill out, and another to build a job command when the user submits the form. You can copy an existing PHP file such as runSimple.php to create your new launch page. To give your page the Appion processing page look and feel with the header and side menu, be sure the functions processing_header($title,$heading,$javascript) and processing_footer() are called.
     
    A starting template with documentation is available here to get you started:
        cp -v runAppionScript.php.template runMyProgram.php

     
2.  **Add a link to your page in the [menuprocessing.php](https://emg.nysbc.org/redmine/projects/appion/repository/changes/trunk/myamiweb/processing/inc/menuprocessing.php) file or from another page**
     
    The menuprocessing file is a bit tricky to work with.
     
3.  **Create a new form class for your package specific parameters**
     
    You can copy simpleParamsForm.inc as a template for your own form parameters. There are 2 primary functions to define.
    1.  Define the constructor
        This is where all your parameters are listed. Values passed into the constructor become default values. Validations can be added to any of the parameters.
    2.  Define the generateForm() function
        This function outputs html. There are many predefined parameter fields that can be used to build your form.
         
4.  **Add pop-up help messages to help.js**
     
    Located at myami/myamiweb/processing/js/help.js.
    1.  Add a new namespace for your form, you can copy the 'simple' section. Don't forget any commas.
    2.  add a help string for each of the parameter keys in your form
    3.  make sure $javascript .= writeJavaPopupFunctions(); is in your createForm() function in your php launch page prior to the processing header function.
         
5.  **Add a publication reference for the package you are using**
     
    1.  Edit /myami/myamiweb/processing/inc/publicationList.inc to include an entry for any references you need to add to your launch page.
    2.  publications can be added to a page with the following code:
                $pub = new Publication('appion'); 
                echo $pub->getHtmlTable(); //returns the html reference to the "appion" publication

        
         
6.  **Use your new form class in your launch page**
     
    1.  Modify the launch page **createForm()** function
        The create form function outputs the html needed for your form. The myami/myamiweb/processing/inc/forms directory holds reusable form classes based on the basicForm.inc class. Any combination of these can be used to add parameters to your form with little knowlege of html. You may also create a new form class to define the parameters specific to your job command.
        1.  Add a call to your form class generateForm() function, adding default values in the constructor.
                    $simpleParamsForm = new SimpleParamsForm('','','','CHECKED','','','10','30','','20','100','2','2','10','','0.8','40','3','3');
                    echo $simpleParamsForm->generateForm();
        2.  Add a reference to your publication
                    $pub = new Publication('appion');
                    echo $pub->getHtmlTable();
    2.  Modify the launch page **createCommand()** function
        1.  instantiate and validate your form parameters
                    $simpleParamsForm = new SimpleParamsForm();
                    $errorMsg .= $simpleParamsForm->validate( $_POST );
        2.  Create your new command
                    /* *******************
                     PART 2: Create program command
                     ******************** */
                    $command = "runSimpleCluster.py ";

                    // add run parameters
                    $command .= $runParametersForm->buildCommand( $_POST );

                    // add simple parameters
                    $command .= $simpleParamsForm->buildCommand( $_POST );
        3.  Add a reference to your publication in the header info
        4.  Change the jobtype passed in showOrSubmitCommand()
