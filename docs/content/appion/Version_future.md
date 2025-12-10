This is the destination for Feature to implement or Bugs to fix that have no specific timeline

1.  **Automated testing** #1005 (Amber) (2 weeks)
    1.  Develop test scripts where possible #1007
    2.  Establish a permanent test data set in Data00
         
2.  **Expand Auto-Installer** #1015 (Amber)
    1.  add processing packages to installer (spider, frealign, eman)
         
3.  **Add modules to pipeline**
    1.  Add Protomo2 (Amber, Eric) #1026
    2.  Add new version of Chimera to existing code to learn what is involved #82 #25
    3.  Chose other modules to add after code changes
    4.  See if StokesLabProcedure will integrate their stuff as a Beta test
         
4.  **Create a developers tutorial** #1022
    1.  Add a developers tab to the appion website with links to all the resources available #1021
    2.  Define coding standards (#10)
        1.  python doc string viewer/editor (#162)
        2.  Edit several key files (such as often copied ones) to use standards rigorously as samples #1012
        3.  PHP standards doc #1013
        4.  python standards doc #231
             
5.  **Features for public cluster** (release with 2.1.1)
    1.  Users need to be able to run imageuploader remotely. (#274)
    2.  Need to be able to define max number of procs per node for each processing host - Advanced version (#366)
    3.  Add single user sign-on functionality for SDSC roll-out (#1010)
    4.  Investigate how data will move between AMI and SDSC (#1011)
    5.  Having a different password for the imageviewer login and the cluster login is confusing. #364
         

### Moved to low priority:

1.  **Expand Auto-Installer** #1015
    1.  multiple servers #1016
    2.  multiple platforms #1017 - Mac (highest priority), Fedora, Suse, Ubuntu
    3.  more options (Advanced vs Novice user) #1018
    4.  yum, rpm ? #1019
         
2.  **Automated testing** #1005 (Amber) (4 weeks)
    1.  Develop unit tests where applicable #1006
    2.  Look into automated GUI test apps #1008
    3.  Static testing for code standards? #1009
         
3.  **Better error reporting**
    1.  Biggest problem is jobs management which could be helped with an agent
    2.  Show jobs that are errors (#603)
    3.  Create an error log (#75)
    4.  Remote cluster recons should not return as done if job failed (#531)
         
4.  **Improve help tools**
    1.  Add links to redmine wiki help pages to appion pages (#666)
    2.  Add pop up dialogs to report pages as well (#516)
    3.  Image viewer tool tips
         
5.  **Create or use an object-relational mapping for PHP** #1020
    1.  Look into Zend library
        1.  [example](http://framework.zend.com/manual/en/zend.db.select.html)
             
6.  **Discuss a strategy to modify database schema without effect external developers.**
    1.  we will wait and address this when someone is ready to make a change.
         
7.  **clean up web interface**
    1.  Remove inconsistencies in web interface (#41 #670)
    2.  Add session name to window so that window are not reloaded from another session (#512)
    3.  Remove select project box in getproject page. (#14)
    4.  Implement sorting algorithm into project management tool. (#13)
    5.  Job Status updates missing on some tools (#994)
    6.  Reorganize the last column in the view project page. (#15)
         
8.  **Leginon**
    1.  Feature to measure focus change in a random direction. (#226)
    2.  import preset by searching for session that uses an application (#654)
    3.  Allow averaging of multiple focus measurements (#225)
    4.  Leginon image viewer should cache the FFT images as well. (#217)
    5.  target queue editor (#214)
         
9.  **misc**
    1.  Data Location tool-find data and push it to external drive (#954)
    2.  Snapshots of projection views for uploaded models. (#857)
    3.  Put variables from config.php into the database (#699)
