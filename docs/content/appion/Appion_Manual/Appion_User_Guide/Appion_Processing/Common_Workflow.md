Appion presents the user with a menu of options for image processing that is dynamically updated as each step is completed. When the user clicks on one of the menu options, Appion generates a new web page specific to the selected operation that requests inputs and allows the user to launch jobs on one of several processing machines or clusters. The job progress is monitored by updates to the menu. The user can check the progress of the job through the logfile, accessible through the the webpages after the job has been launched. Additionally, the user can kill the job from the webpage by clicking on the "kill job" button when viewing the logfile ([note: if the job is manually killed from the terminal, the database does NOT get updated. The user must manually run the updateAppionDB.py script [updateAppionDB.py jobid status [projectid]], e.g. "updateAppionDB.py 1234 D 1"]{.underline}) Once a completed job shows up in the menu, the user may click on its entry to generate a web page that reports on the results. Most input options are provided with defaults. Help options for each input are provided as pop-ups on the Appion web pages. Detailed step-by-step instructions for most of the procedures are available within the Appion documentation.

## 1. [Step by Step Guide to 3D Reconstruction in Appion](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Step_by_Step_Guide)

## 2. [Quality Assessment and Processing Output pages in Appion](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Quality_Assessment)

## 3. [Random-Conical Tilt Reconstruction Workflow in Appion](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Random-Conical_Tilt_RCT_Reconstruction_workflow)

## 4. [Fab-labeled trimers processing Workflow in Appion](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Trimer_processing_workflow)

![](images/Picture_81.png)
![](images/Picture_83.png)

[< Terminology](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Terminology) | [Step by Step Guide >](/appion/Appion_Manual/Appion_User_Guide/Appion_Processing/Common_Workflow/Step_by_Step_Guide)
