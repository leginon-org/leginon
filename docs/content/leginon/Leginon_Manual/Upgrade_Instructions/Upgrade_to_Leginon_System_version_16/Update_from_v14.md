Follow update instruction for update from v1.5. In addition, clean up leginon and sinedo
configuration as instructed here whether your installation is on Windows or Linux.

## Clean up leginon.cfg:

Sinedon now have full control of database interaction, therefore, the database
configuration in leginon.cfg is no longer needed.

-   Modify your leginon.cfg in your home directory to REMOVE the following:


    [Database]
    host:[your_host]
    name: <link linkend="db_example_names">dbemdata</link>
    user: <link linkend="db_example_names">usr_object</link>
    passwd:

## Configure sinedon.cfg:

Since Leginon 1.5 release, Sinedon configuration can either be globally configured by
including sinedon.cfg with the sinedon installation or overwriten by users by including the
same-named file in his/her home directory.

See sinedon configuration subsection in Complete
Installation Chapter.

[Upgrade to Leginon System version 16 ^](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_16)
