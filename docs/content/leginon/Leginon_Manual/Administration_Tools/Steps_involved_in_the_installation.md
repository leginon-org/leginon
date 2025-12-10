See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and the Leginon Forum searching for "admin" if you run into problems.

## Go to administration page

Open a web browser. Go to 'http://yourhost/myamiweb/admin.php'
If the login system is activated, you will have to log in as administrator user. its password is the same as the username if you used autoinstaller.

If you are using installed using the auto-installation script or myamiweb setup wizard, you should have a number of default groups and users already in your database:
> **Note:** See external reference `appion:default_groups`

> **Note:** See external reference `appion:default_users`

# 1. Change Leginon/Appion Administrator password

This user has access to everything. You need to keep it for setting default settings. Don't delete it. However, its password is the same as the host root password if you used autoinstaller. Therefore, if you want to change it for production, just choose the user, make the change, and then submit.

# 2. Add yourself as a User


A Leginon user set in the adminstration tool defines his/her own preferences once changed from the "adminstrator" user default above. It is also not related to the computer login user. Therefore, it is is necessary to go through the following steps to set up an existing computer user as a new Leginon user. With login feature activated in myamiweb, this user is also used for logging into the web server to see and process data belong to him/her:

## Add a User From Administration web page

- Open a web browser. Go to 'http://yourhost/myamiweb/admin.php'.

- Click on Users.

- Click on Add A New User (Only users in Administrator group can do this if login feature is activated)

- Add a "username" (required) for the user. (This is like a one-word username that people use to log into a computer).

- Enter all required information.

- Add this user to a previously created group. Or, add a new group for this user. (required)

- Click Save.

![](images/user_on.png)

![](images/admin_usertable.png)

## Create individual configuration if not set globally

- Copy [leginon.cfg](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg) from an existing user to the home directory of the new user.

- Modify leginon.cfg

Modify the [user] "Fullname" field in **leginon.cfg** to correspond to the "firstname"+" "+"lastname" fields in the Leginon Administration User Tools.


# 3. Import Applications

-   Click on Applications.

![](images/application_on.png)

**If you have used auto-installation tool to install, you should have a few applications imported already. These include Calibrations, Manual, and a few flavors of MSI applications.**

-   Enter the name of the Leginon application XML file. These are files in a subdirectory of your leginon installation called "applications" starting from Leginon v1.3.

> The most commonly used Leginon applications are included as part of the Leginon download. These XML files are in subdirectory of your Leginon download and installation called "applications". The XML files should be imported using the web based application import tool. Each application includes a version number "(1.5)" in its name to indicate the MInimal Leginon version that it will work with.

**If your system uses [separate computer to control the digital camera from the one controlling the scope](/leginon/Using_Leginon_on_a_system_where_the_microscope_and_camera_are_controlled_by_different_computers), please use the application that carries "2" in its name, such as MSI-T2. Otherwise, import ones without the "2", such as "MSI-T"**

> To find Leginon installation path on Linux:

     >start-leginon.py -v

-   ![](images/admin_apptable.png)


-   Select the name of the "To" Host the application will be imported to.


-   Click Import.

# 3. Import Additional Application Settings

For some of the newer applications, you may find json files in /your_git_clone/leginon/applications. These should be imported if you imported the application with the same name.
See [Import Export Application Settings as json file](/leginon/Leginon_Manual/Create_and_Edit_Applications/Import_Export_Application_Settings_as_json_file)

# Proceed to Next Chapter to [Add a new project for testing installation](/leginon/Leginon_Manual/Using_Project_Management_Tools/Add_a_new_project_for_test)

The rest of this chapter is for references.

Installation instruction: [Add a new project for testing installation >](/leginon/Leginon_Manual/Using_Project_Management_Tools/Add_a_new_project_for_test)
Chapter thread: [< Recommandation for setup at a new institute](/leginon/Leginon_Manual/Administration_Tools/Recommandation_for_setup_at_a_new_institute) | [Set up for a new regular user >](/leginon/Leginon_Manual/Administration_Tools/Set_up_for_a_new_regular_user)
