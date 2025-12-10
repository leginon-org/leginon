mysqldump is a tool comes with mysql installation that creates mysql commands that can reproduce the database when executed on a different host.

If you run into problems that you can not decribe the history of getting there to leginon team, this might be the best way for us to dicover what went run.
You will need help from the person who installed the packages if you don't know what the name of the databases are and the mysql user that have the permission to do this.
A hint: the information is in sinedon.cfg

Once these are figured out, here is the command using our standard naming used in this wiki.

## whole leginon and project databases

    mysqldump -h your_host -u usr_object -p leginondb > your_leginondb_dump.sql
    mysqldump -h your_host -u usr_object -p projectdb > your_projectdb_dump.sql

Each of these commands will ask you for the password.

## Individual table

That's say you want to dump FocuserSettingsData table from leginon database that is called leginondb, you should do

    mysqldump -h your_host -u usr_object -p leginondb FocuserSettingsData > your_table_dump.sql

For multiple tables, append them at the end like this example where we dump all focuser related tables.

    mysqldump -h your_host -u usr_object -p leginondb FocuserSettingsData  FocusSettingsData FocusSequenceData > your_focuser_dump.sql

[Load the saved databases >](/leginon/Leginon_Manual/Trouble_shooting/Load_mysqldumped_databases)
