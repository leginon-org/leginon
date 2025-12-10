This algorithm is faster than ACE 1 and includes astigmatism estimation.

![](images/Picture_17.png)

## General Workflow:

1.  Make sure that appropriate run names and directory trees are specified. Appion increments names automatically, but users are free to specify proprietary names and directories.
2.  Select the leginon preset corresponding to the images you'd like to process. Generally "_en" images in leginon are the raw micrographs, but uploaded film data will have a different present. Selecting "all" will simply process all images.
3.  Check boxes allow the option to run Ace 2 concurrently with data collection. "Wait for more images" will wait until collection times out before stopping ACE 2 processing. The "Limit" box allows restrictions on the number of images to process, which is useful when testing parameters initially.
4.  Radio buttons under "Images to Process" allows a level of pre-processing image filtering. Images that were rejected, hidden, or made exmplars in the image viewer can here be included or exluded.
5.  Radio buttons under "Image Order" sets the order in which images are processed and radio buttons under "Continuation" gives the option of continuing or rerunning a previous ACE 2 run.
6.  If you have a previous ACE1 or Ace 2 run, check this box and set a confidence value to reprocess images that scored below that confidence value. Otherwise, leave unchecked.
7.  Make sure that "Commit to Database" box is checked. (For test runs in which you do not wish to store results in the database this box can be unchecked).
8.  Click on "Run Ace 2" to submit your job to the cluster. Alternatively, click on "Just Show Command" to obtain a command that can be pasted into a UNIX shell.
    ![](images/Picture_34.png)
9.  If your job has been submitted to the cluster, a page will appear with a link "Check status of job", which allows tracking of the job via its log-file. This link is also accessible from the "1 running" option under the "Run Ace 2" submenu in the appion sidebar.
10. Now click on the "1 Complete" link under the "Run Ace 2" submenu. This opens a summary of all CTF Estimation (Ace 1, Ace 2, CtfFind) runs with a summary histogram of confidence values.
    ![](images/Picture_35.png)
11. Clicking on "download ctf data" opens a dialog for exporting CTF Estimation results for use in another application.
12. Clicking on the "acerun#" name opens a summary page of the parameters used for the particular run.
13. The CTF parameters and astigmatism estimation determined by Ace 2 can be applied to particles during particle boxing in appion with the [Create Particle Stack](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Stacks/Stack_Creation) tool.
    ![](images/Picture_22.png)

## Notes, Comments, and Suggestions:

1.  Ace 2 is faster than ACE 1
2.  If multiple CTF estimation runs are performed for a single dataset, the Appion stack creation tool will select the CTF parameters determined with the highest confidence value (regardless of algorithm used) for a particle from a given micrograph.

[< CTF Estimation](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/CTF_Estimation) | [Create Particle Stack >](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Stacks)
