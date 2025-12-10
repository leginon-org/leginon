See [Installation Troubleshooting](/leginon/Leginon_Manual/Installation_Troubleshooting) and [Leginon Forum](http://emg.nysbc.org/redmine/projects/leginon/boards/6) searching for "admin" if you run into problems.

## Go to administration page

Open a web browser. Go to 'http://yourhost/myamiweb/admin.php'
If the login system is activated, you will have to log in as administrator user.

## Add yourself as a User

[Set up for a new regular user shared](/leginon/Set_up_for_a_new_regular_user_shared)


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

[< Steps involved in the installation](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation) | [More about Groups >](/leginon/Leginon_Manual/Administration_Tools/More_about_Groups)


## Import Applications

-   Click on Applications.

![](images/application_on.png)

-   Enter the name of the Leginon application XML file. These are files in a subdirectory of your leginon installation called "applications" starting from Leginon v1.3.

> The most commonly used Leginon applications are included as part of the Leginon download. These XML files are in subdirectory of your Leginon download and installation called "applications". The XML files should be imported either using the web based application import tool. Each application includes "(1.5)" in its name to indicate that it will work with this new version of Leginon. The applications that carry the older version name are compatible with the older Leginon.

> To find Leginon installation path on Linux:

     >start-leginon.py -v

-   ![](images/admin_apptable.png)


-   Select the name of the "To" Host the application will be imported to.


-   Click Import.

## Proceed to First Leginon Test Run Chapter

[Leginon test runs](/leginon/Leginon_Manual/Start_Leginon/Test_Leginon_with_Simulator) test for tem/ccd controls and network communications. The rest of this chapter is for references.
