-   Click on a project name on the webpage `http://your_host/myamiweb/project/project.php`. This will take you to a new webpage `http://your_host/myamiweb/project/getproject.php?pId=1`. The number following "pId=" depends on the project id automatically assigned to the project.
-   At the end of the Info table, you should see:


    processing db: not set (create processing db) db name ap1

You can create the default numbered style database ap... or give it a new name with the same prefix. If you want to specify a database name that does not use the default prefix, please note that your db user specified in the config.php in project_1_2 needs to have the necessary privileges for that database. You may additionally want to change the value assigned to $DEF_PROCESSING_PREFIX in project_1_2/config.php if you want to use your new prefix all the time.

-   Enter the processing database name and click "create processing db".
-   The page should refresh and display the linked database like this:


    processing db: ap1

See next section on trouble shooting if you get the original page instead.

-   **Repeat the above process for all your projects.**

If you want all your processing databases combined in one single database (not recommended, as this becomes large very fast), just use the same name for all your projects.

The above procedure not only creates the database, but also create some of the tables that you need to start processing.
