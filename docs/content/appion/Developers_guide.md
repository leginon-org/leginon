This guide is primarily intended to help noobs to both Appion and Programming in general get up and running in the development environment that we have created at AMI.
It is a good place to add notes, however basic, that may help someone else accomplish a task related to Appion software development.
Parts of this guide are specific to machines and the environment that we have at AMI. Our apologies.

1.  **System Overview**
    1.  Leginon
        1.  Scope
        2.  Windows Machine
    2.  Appion
        1.  Web Parts - web server
        2.  Python Parts - processing server
        3.  3rd party apps
    3.  Clusters
    4.  [Myami code module diagram](/appion/Developers_guide/Myami_code_diagram/)
         
2.  **Development Tools**
    1.  [Redmine quick start](/appion/appionAMI_Redmine_Quick_Start_Guide) - issue reporting and adding documentation
    2.  [Eclipse quick start](/appion/Developers_guide/AMI_Eclipse_Quick_Start_Guide) - setting up an integrated development environment
    3.  [Subversion](/appion/Developers_guide/Subversion) (SVN) - Tips for using our code repository (pre 3.3)
    4.  [Git](/appion/Developers_guide/Git) (GIT) - Tips for using our repository (3.3+ and development trunk)
         
3.  **Language and Technology Resources**
    1.  language specific tutorials, guides and tips
        1.  [HTML notes](/appion/HTML_notes)
        2.  [CSS notes](/appion/Developers_guide/CSS_notes)
        3.  [PHP notes](/appion/Developers_guide/PHP_notes)
        4.  [Python notes](/appion/Developers_guide/Python_notes)
        5.  [Javascript notes](/appion/Developers_guide/Javascript_notes)
    2.  [General Best Practices](/appion/Developers_guide/General_Best_Practices)
    3.  [AMI's best practices](/appion/Coding_standards)
    4.  [Object Oriented Programming](/appion/Developers_guide/Object_Oriented_Programming)
    5.  [Useful shell commands](/appion/Developers_guide/Useful_shell_commands)
    6.  [Getting started with MySQL](/appion/Developers_guide/MySQL_Notes)
         
4.  **Installing Appion for development**
    1.  Running the code from your sandbox
         
5.  **Adding a new program to the pipeline**
    1.  General Instructions
        1.  Processing parts (Python)
            1.  database access
        2.  Web Parts (PHP)
            1.  [Adding an Appion job launch page](/appion/Developers_guide/How_to_add_an_AppionLoop_GUI_page)
            2.  reporting page
                1.  [Using basicReport.inc](/appion/Developers_guide/Using_basicReportinc) for very simple PHP report pages
            3.  database accesss
    2.  Adding a refinement method (single and multi model) or any other method that requires a specialized job file to submit to a cluster
        1.  [Overview of launching, running, and uploading cluster jobs](/appion/Developers_guide/Cluster_job_overview)
        2.  [Python wrapper for 3rd party programs](/appion/Developers_guide/Adding_refine_python_parts) (Anchi)
        3.  [Modifications to runJob.py](/appion/Developers_guide/Adding_refine_runjob) (Christopher)
        4.  [Uploading results to the databse](/appion/Developers_guide/How_to_add_a_new_refinement_method) (Dmitry)
        5.  [Adding the user interface](/appion/Developers_guide/Refine_Refactor_documentation) (Amber)
             
6.  **Testing**
    1.  [Test datasets at AMI](/appion/Developers_guide/Test_datasets_at_AMI)
    2.  [Create Appion Session for testing purposes](/appion/Create_Appion_Session)
    3.  [How to set up AMI databases on your local machine](/appion/Developers_guide/Setup_Local_Databases_): Handy if you want to play with the databases without affecting anyone else.
    4.  [Automated testing](/appion/Developers_guide/Appion_Testing)
    5.  [How to test upload images with your own sandbox](/appion/Developers_guide/How_to_test_upload_images_with_your_own_sandbox)
    6.  [How to run manual picking and mask making](/appion/How_to_run_manual_picking_and_mask_making)
         
7.  **Error Handling**
    1.  [Error handling guide](/appion/Developers_guide/Error_Handling)
         
8.  **Adding pop-up Help**
    1.  [adding popup help](/appion/adding_popup_help)
         
9.  **Making changes to database tables**
    1.  [Database change procedure](/appion/Database_change_procedure)
         
10. **Other stuff**
    1.  [Deprecated instructions for adding an Appion job launch page](/appion/Developers_guide/How_to_add_a_launch_page)
    2.  Where to find help
    3.  [Appion tricks](/appion/Developers_guide/Appion_tricks)
    4.  [Common variables used](/appion/Developers_guide/Common_variables_used)
    5.  Appion Developer's Workshops
        1.  [2010 Appion Developer Workshop](/appion/2010_Appion_Developer_Workshop)
        2.  [2011 Appion Developer Workshop](http://emg.nysbc.org/redmine/projects/appion-workshop/wiki)
11. [Job submission vs direct Appion Script running from terminal](/appion/Job_submission_vs_direct_Appion_Script_running_from_terminal) What are the differences in database logging and resource usage.
