The following assumes that you are going to use the autoinstalled computer as your database, webserver, and processing server but save the files somewhere else.

1.  (Optional but recommended) Create a non-root mysql user with access privilege to operate various databases. See [Database Server Installation](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation)
    1.  Follow the section "Create user", and use Option 1 or 2 is enough.
    2.  Follow the section "Give create and access privileges for the processing databases which begin with "ap" in the same wiki page.
    3.  If Option 1 is used in the the user previlege above, follow [leginon:Additional Database Server Setup after Web Server Installation](/appion/leginonAdditional_Database_Server_Setup_after_Web_Server_Installation)
2.  Change the default paths to your network storage disk and give permission to the linux user who will run appion python scripts the permission to read and write to it. See [File Server Setup Considerations](/appion/Appion_Manual/Complete_Installation/File_Server_Setup_Considerations) for how the path should be set up
    1.  Change the global /etc/myami/leginon.cfg in the module "Images". See [Configure leginoncfg](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg) for more detail
            [Images]
            path: /your_storage_disk_path/leginon
    2.  (Optional) If the default directory appion run are placed under does not follow what is described in [File Server Setup Considerations](/appion/Appion_Manual/Complete_Installation/File_Server_Setup_Considerations), you will need to modify /var/www/html/myamiweb/config.php to define DEFAULT_APPION_PATH. Search the syntex in the file and uncomment it to read
            define('DEFAULT_APPION_PATH',"/your_other_sotrage_disk/appion");
