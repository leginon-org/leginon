If your webserver installation is successful, a number of tables will be propagated in the databases. There were several options for setting up database user privileges recommended in [Database Server Installation](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation). The following additional steps should be taken, depending on which option you previously used.

-   **Option 1: More secure - Restrict Drop and Delete priviledges**
     
    If you are using the more secured privilege settings we recommended in [Database Server Installation](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation), you should expand the privileges of these three tables at this point:
     
        GRANT DELETE ON leginondb.ViewerImageStatus TO usr_object@'localhost';
        GRANT DELETE ON projectdb.shareexperiments TO usr_object@'localhost';
        GRANT DELETE ON projectdb.projectowners TO usr_object@'localhost';
        GRANT DELETE ON projectdb.processingdb TO usr_object@'localhost';

    
    If you use Leginon to do robotic grid screening, you will also need to do the following to grant delete privileges to the these tables at the mysql prompt:
        GRANT DELETE ON projectdb.gridboxes TO usr_object@'localhost';
        GRANT DELETE ON projectdb.grids TO usr_object@'localhost';
        GRANT DELETE ON projectdb.gridlocations TO usr_object@'localhost';


-   **Option 2: Less secure - Allow all privileges**
     
    If you are allowing all privileges, no further steps need to be taken.


-   **Option 3: Allows access from all computers in the domain**
     
    You may choose to assign a domain to your commands and use a wildcard to allow access from all computers in the domain.
     
        GRANT DELETE ON leginondb.ViewerImageStatus TO usr_object@'%.mydomain.edu';
        GRANT DELETE ON projectdb.processingdb TO usr_object@'%.mydomain.edu';

    
    Again, if you use Leginon to do robotic grid screening, you may want to grant delete privileges to the these tables at the mysql prompt:
        GRANT DELETE ON projectdb.gridboxes TO usr_object@'%.mydomain.edu';
        GRANT DELETE ON projectdb.grids TO usr_object@'%.mydomain.edu';
        GRANT DELETE ON projectdb.gridlocations TO usr_object@'%.mydomain.edu';
