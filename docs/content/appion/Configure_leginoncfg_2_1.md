## The order in which Leginon/Appion looks for leginon.cfg

1.  individual user home directory
2.  $PYTHONSITEPKG/leginon/config
     
    Note: You can discover the $PYTHONSITEPKG path by starting python:
        python
        import sys
        sys.path

    
    The first path to site-packages should hold the config file.

## configuration file template

A skeleton (default) configuration file is available:

    $PYTHONSITEPKG/leginon/config/default.cfg


where $PYTHONSITEPKG is your python site-packages directory

## Create a global leginon.cfg

Copy default.cfg to leginon.cfg.

    sudo cp -v $PYTHONSITEPKG/leginon/config/default.cfg $PYTHONSITEPKG/leginon/config/leginon.cfg

Edit the newly created file and add a directory for images. Make sure you have permission to save files at this location. See [File Server Setup Considerations](/appion/Appion_Manual/Complete_Installation/File_Server_Setup_Considerations) for more details

You may put in a fake path on the microscope PC installation and ignore the error message at the start of Leginon if you follow our general rule of not saving any image directly from the microscope pc,

    [Images]
    path: your_storage_disk_path/leginon
