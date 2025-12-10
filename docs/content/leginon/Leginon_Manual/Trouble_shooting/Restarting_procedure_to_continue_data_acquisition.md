1.  main> restart Leginon by 'start-leginon.py'
     
2.  Leginon Setup Wizard> Select user and returning sesson and "Start" the program.
     
3.  Leginon/Application> select the application used to run. Select the scope and the main launcher, and then launch the application.
     
4.  If a simple application such as "Manual" is used, just continue what you were doing.
     
5.  If some "MSI" application is used and Leginon did not crash during queue processing, do the following to continue:
     
    -   Leginon/Square Targeting/Toolbar/Tiles![](images/tiles.png)> select the current mosaic from the pull-down list by checking the ID and label, and then "Load" it.
         
    -   Leginon/Square Targeting/Toolbar> "Submit" ![](images/play.png) the target list that is loaded with the atlas. Leginon will check the status of the target acquisition and processing and pick it up from where it was left off.
         
6.  If some "MSI" application is used and Leginon crash during queue processing, do the following at the node where the targets from its queue you wish to continue process.
     
    Leginon/XXX Targeting/Toolbar> click on the "Submit the queued target" ![](images/send_queue_out.png).

## None of the above will resume data collection if all targets are done or abort by the user. Select new ones on the atlas for more data collection.

[< Aborting targets that are not yet being processed](/leginon/Leginon_Manual/Trouble_shooting/Aborting_targets_that_are_not_yet_being_processed) | [General operation problems >](/leginon/Leginon_Manual/Trouble_shooting/General_operation_problems)
