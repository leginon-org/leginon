This application is meant to demonstrate how to create applications with event bindings in Leginon. This application has little functionality other than being able to take one image at a time at a given preset.

-   Create a blank Leginon application called "Simple Application." Refer to [Use the Application Editor to create Leginon applications](/leginon/Leginon_Manual/Create_and_Edit_Applications/Use_the_Application_Editor_to_create_Leginon_applications) to create this blank application and for help with the instructions below.


-   Add two launchers with the aliases "scope" and "main."


-   Add nodes with the aliases listed in the table below.


-   Add event bindings according to the table below.


-   Rename the application "Simple Acquisition."


-   Click Apply and Save.

### Table 18.1. Simple Application Nodes:

  Node Class:         Node alias:   Launcher:
  ------------------- ------------- -----------
  Corrector           cor           main
  SimpleAcquisition   simple_acq    main
  PresetsManager      pm            main
  EM                  em            scope

### Table 18.2. Simple Application Event Bindings:

  Node to alias:   Event Binding:       Node from alias:
  ---------------- -------------------- ------------------
  pm               ChangePresetEvent    simple_acq
  simple_acq       PresetChangedEvent   em

[< Import/Export Application Settings as json file](/leginon/Leginon_Manual/Create_and_Edit_Applications/Import_Export_Application_Settings_as_json_file) | ["Calibrations" Application >](/leginon/Leginon_Manual/Create_and_Edit_Applications/Calibrations_Application)
