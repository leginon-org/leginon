## Don't forget to perform [TEM Scripting Beam Tilt Calibration](/leginon/Leginon_Manual/Instrument_Set-up/Calibrations_required_on_FEI_microscopes/TEM_Scripting_Beam_Tilt_Calibration) for your FEI microscope

## [Import new applications from your myamiweb administration page](/leginon/Leginon_Manual/Administration_Tools/Applications) if desired.

-   Calibrations (2.0) application contains a new node with various imaging options useful for coma-free alignment required before calibrate Leginon fore automated coma-free alignment.

## Start Leginon and [reacquire all gain references](/leginon/Leginon_Manual/Leginon_Calibrations_Application/Bright_and_Dark_reference_images).

-   Old dark and bright references can not be used with the new version.

## If you have chosen to enable the [myamiweb login feature](/leginon/appionWhat_does_User_Authentication_do_to_myamiweb) during web server upgrade, you have to go through the following steps to make it usable to individual Leginon user in the way you specified:

1.  Go to http://yourhost/myamiweb page
2.  Log in as administrator. As default during the upgrade, a password identical to the username was temporarily assigned so that you can login.
3.  Change the user profile of the administrator and change the password so that it is not so obvious.
4.  Check profile of each Leginon user group at 'http://yourhost/myamiweb/addgroup.php'. Add groups and/or reassign group privilege if desired.
5.  Check profile of each Leginon user at 'http://yourhost/myamiweb/user.php'. Reassign to a different group if desired.
6.  Click on the project icon to [go to project management tool page](/leginon/Leginon_Manual/Using_Project_Management_Tools/Go_to_project_tools_page)
7.  For each existing project, click on the project name to [Edit an existing project](/leginon/Leginon_Manual/Using_Project_Management_Tools/Edit_an_existing_project)
    1.  Click on the **Edit** link besides the owner list to add new owners for the project.
    2.  For each user who does not belong to a group with administrator privilege but requires access to the particular project, add he/she as an owner.
    3.  Return to project summary page by clicking on "View Project" icon
8.  Have each Leginon user log in to http://yourhost/myamiweb and add their e-mail address to his/her profile and modify the password to something better than the default. The password in the database is encrypted. The e-mail address is used to send the user his/her forgotten password.

[< How to Update from v1.6 (Microscope Windows Computer)](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_2x_from_version_16/How_to_Update_from_v16_Microscope_Windows_Computer)
