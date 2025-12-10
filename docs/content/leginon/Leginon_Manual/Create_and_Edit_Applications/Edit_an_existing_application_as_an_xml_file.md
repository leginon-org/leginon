Application editor behaves well enough that it is not necessary to edit xml files. However, if you want to, here is how.

1.  go to "http://your_myamiweb/addapp.php" with your web browser
2.  Choose your existing application from Export section and export and save as an xml file.
     
3.  Edit the xml file in any text editor.
     
    Search for the name of the node class that you want to replace and make the changes.
     
    The following section of the file controls the name of the application and version number
        <!-- ApplicationData -->

        <sqltable name="ApplicationData">

        <field name="DEF_id" >264</field>

        <field name="version" >6</field>

        <field name="DEF_timestamp" >20041209145648</field>

        <field name="name" >MSI-raster (1.0)</field> </sqltable>

    
    Change the application name in the "name" field as a new application
     
4.  Use the same webpage to import: Load the changed application xml file in the Import section and click import button.

[< Use the Application Editor to create or edit Leginon applications](/leginon/Leginon_Manual/Create_and_Edit_Applications/Use_the_Application_Editor_to_create_Leginon_applications) | [Import/Export Application Settings as json file >](/leginon/Leginon_Manual/Create_and_Edit_Applications/Import_Export_Application_Settings_as_json_file)
