For older versions of Appion and Leginon (pre-2.2), please use the following instructions:
[Instructions for Appion and Leginon versions prior to 2.2](/appion/Configure_leginoncfg_2_1)

## The order in which Leginon/Appion looks for leginon.cfg

1.  individual user home directory
2.  where leginon python modules are loaded from. In an installed case, $PYTHONSITEPKG/leginon
     
    Note: You can discover the $PYTHONSITEPKG path by starting python:
        python
        import sys
        sys.path

    
    The first path to site-packages should hold the config file.
     
3.  /etc/myami (on Unix)

## Locate the search directories and the currently loaded cfg files by running the following python script in $PYTHONSITEPKG/leginon

    configcheck.py

## Configuration file template

A skeleton (default) configuration file is available:

    /path/to/myami/leginon/leginon.cfg.template

## Create a global leginon.cfg

Copy leginon.cfg.template to leginon.cfg.

    sudo cp -v /path/to/myami/leginon/leginon.cfg.template /etc/myami/leginon.cfg

Edit the newly created file and add a directory for images. Make sure you have permission to save files at this location. See [File Server Setup Considerations](/appion/Appion_Manual/Complete_Installation/File_Server_Setup_Considerations) for more details

You may put in a fake path on the microscope PC installation and ignore the error message at the start of Leginon if you follow our general rule of not saving any image directly from the microscope pc,

    [Images]
    path: /your_storage_disk_path/leginon
