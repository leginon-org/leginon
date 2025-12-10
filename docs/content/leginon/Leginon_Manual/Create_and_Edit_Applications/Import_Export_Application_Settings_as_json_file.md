We have a pair python scripts used for exporting and importing application settings in your_myami/dbschema/tools.
You need to run this on your leginon linux station where leginon is installed so it can find the python library.

## Export to json file

Once you have a session that successfully use the settings that you would like to distribute

    cd /your_myami/dbschema/tools
    python ./export_leginon_settings.py <sessionname> <optional partial application name> <optional node name prefix>

The options means that you could export the settings specific to the application, or node.

## Import into database

The settings needed for the application can be imported into Leginon

    cd /your_myami/dbschema/tools
    python ./import_leginon_settings.py <your_application name>


It will prompt you for location of the settings json file if it can not find it automatically.
The default location of the file is /your_myami/leginon/applications/your_application.json

## Edit json file for a different node name

If you copy an application with application editor and changed the node alias to match your local naming convention, the settings get default back to the class default. You can modify the json file exported from the old application and modify it to match the new naming convention.

For example, the json section for "Presets Manager" is

      {
        "PresetsManagerSettingsData":{
          "stage always":true,
          "name":"Presets Manager",
          "xy only":true,
          "pause time":1.0,
          "apply offset":false,
          "smallsize":1024,
          "mag only":false,
          "blank":false,
          "optimize cycle":true,
          "isdefault":true,
          "cycle":true
        }
      },

You can change the name field to corresponds to the new node name. When it is imported as shown above, it shoud import into the new node and application.

[< Edit an existing application as an xml file](/leginon/Leginon_Manual/Create_and_Edit_Applications/Edit_an_existing_application_as_an_xml_file) | [Create Leginon "Simple Application" >](/leginon/Leginon_Manual/Create_and_Edit_Applications/Create_Leginon_Simple_Application)
