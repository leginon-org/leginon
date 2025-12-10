## How to move a Leginon session to a different Appion project (before any processing has been done)

1.  Find the **projectexperiments** table in the **project** database. This relates the Leginon sessions with appion projects and is the only place where a change needs to be made.
2.  Find the session id. In the web tools Project DB interface, browse to the project that currently holds the session and note the session id number of the session you wish to move.
3.  Find the old project id and the new project id. Look at the URL in the web browser while viewing the project. You should see "projectId=327" at the end of the url. The integer number is the project id to note. This number may also correspond to the appion database name (ex. ap327).
4.  In the **projectexperiments** table, search for the entry for your session and confirm the current project id is listed in its entry. Then edit the entry to include the new project id.
5.  Browse to the new project in the web interface and confirm the session is listed under the desired project.
