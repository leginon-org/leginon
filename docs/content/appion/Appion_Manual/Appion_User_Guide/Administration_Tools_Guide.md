After a new installation, you will have to input Groups,Users and Instrument to the database you have just created. Applications will need to be imported, too. These tasks can be performed through the web-based Administration Tools.

## Recommandation for setup at a new institute

## First user : administrator

The user named "administrator" is a special user in Leginon. Once the setting preferences in a node that shares the same class and alias are defined by the administrator, all newly created users get these settings when they launch the node until they make changes themselves. This allows a faster setup per database (institute) for the beginners. Therefore, the first user should be named as "administrator" and it should be used normally to ensure the stability of these default preferences.

## Additional users :

A Leginon user set in the adminstration tool defines his/her own preferences once changed from the "adminstrator" user default above. It is also not related to the computer login user. Therefore, it is is necessary to go through the steps outlined in "Set up for a new regular user" section.

## Steps involved in the installation

See Installation Troubleshooting and [Leginon Bulletin Board](http://emg.nysbc.org/bb/viewforum.php?f=2) searching for "admin" if you run into problems.

## Go to administration page

Open a web browser. Go to http://localhost/myamiweb/admin.php

## Add a Group

Groups are used to associate users together. At the moment, Leginon does not use the group association for anything.

-   At http://localhost/myamiweb/admin.php, click on Groups.


-   Add a "name" (required) for the group.


-   Optionally enter a full name for the group.


-   Click Save.

## Add Adminstrator User

-   At http://localhost/myamiweb/admin.php, click on Users.


-   Add "administrator" as the user.


-   Enter a full name as "administrator". This name should be typed exactly as it is (case-sensitive).


-   Add this user to a previously created group.


-   Click Save.

## Add your mircoscope as an TEM instrument

-   Click on Instruments.


-   Add a "name" (required and not arbitrary---FEI tecnai/polara/spirit series are all called "Tecnai") for the microscope. Follow the cases! (a unix requirement)


-   Enter the hostname of the microscope. Do not captalize the characters!!! (a Window's requirement)


-   Select instrument type TEM.


-   Click Save.

## Add your CCD camera as an CCDCamera instrument

-   Click on Instruments.


-   Add a "name" for the camera (required and not arbitrary---Gatan cameras are all called "Gatan"/Tietz cameras all have different names). Follow the cases! (a unix requirement)

See the section on Instrument Tool for more details.

-   Enter the hostname of the microscope. Do not captalize the characters!!! (a Window's requirement)


-   Select instrument type CCDCamera.


-   Click Save.

## Load the default settings of Legion nodes

-   Click on Default Settings.


-   Click on Load.

## Import Applications

-   Click on Applications.

![](images/application_on.png)

-   Enter the name of the Leginon application XML file. These are files in a subdirectory of your leginon installation called "applications" starting from Leginon v1.3.


The most commonly used Leginon applications are included as part of the Leginon download. These XML files are in subdirectory of your Leginon download and installation called "applications". The XML files should be imported either using the web based application import tool. Each application includes "(1.5)" in its name to indicate that it will work with this new version of Leginon. The applications that carry the older version name are compatible with the older Leginon.

To find Leginon installation path on Linux:

     >start-leginon.py -v

On Windows, You should find a shortcut to your Leginon installation folder in the "Start Menu/All Programs/Leginon". If not, it is likely

    C:\Python25\Lib\site-packages\Leginon


-   ![](images/admin_apptable.png)


-   Select the name of the "To" Host the application will be imported to.


-   Click Import.

## Proceed to First Leginon Test Run Chapter

Leginon test runs test for tem/ccd controls and network communications. The rest of this chapter is for references.

## Set up for a new regular user

A Leginon user set in the adminstration tool defines his/her own preferences once changed from the "adminstrator" user default above. It is also not related to the computer login user. Therefore, it is is necessary to go through the following steps to set up an existing computer user as a new Leginon user:

## Add a User From Administration web page

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Users.


-   Add a "name" (required) for the user. (This is like a one-word username that people use to log into a computer).


-   Optionally enter a full name for the user. (required)


-   Add this user to a previously created group. Or, add a new group for this user. (required)


-   Click Save.

![](images/user_on.png)

![](images/admin_usertable.png)

## Get a copy of the configuration files

Copy leginon.cfg and sinedon.cfg (if not set globally for all users) from an existing user to the home directory of the new user.

## Modify leginon.cfg

Modify the [user] "Fullname" field in `<command moreinfo="none">leginon.cfg`</command> to correspond the "full name" field in the Leginon Administration User Tools.

## More about Groups

Groups are used to associate users together. At the moment, Leginon does not use the group association for anything.

## Add/Edit a Group

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Groups.


-   Add a "name" (required) for the group.


-   Optionally enter a full name for the group.


-   Click Save.

## Remove a Group

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Groups.


-   Highlight a group name from the list of created Groups.


-   Click Remove.

![](images/group1_on.png)

![](images/admin_grouptable.png)

## More about Instruments

This is used to add details about the microscope and CCD Leginon will be connected to. More than one instrument can be added with different configurations. The "import" function is useful if the instrument information has been stored on different machines in different Leginon databases.

## Valid Instrument Names

TEM names:

-   Tecnai

Camera names:

-   Gatan


-   Tietz SCX


-   Tietz PXL


-   Tietz PVCam


-   Tietz PVCam


-   Tietz FastScan


-   Tietz FastScan Firewire


-   Tietz FC415


-   Tietz Simulation

## Add/Edit an Instrument

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Instruments.


-   Add a "name" (required and not arbitrary, see the above section) for the microscope or camera.


-   Enter the hostname of the microscope. The domain suffix need not be entered if all machines are under the same hostname.


-   Select instrument type.


-   Click Save.

## Remove an Instrument

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Instruments.


-   Highlight an instrument name from the list of created instruments.


-   Click Remove.

## Import an Instrument Pair

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Instruments.


-   Select a From Host and the name of the Instruments.


-   Click Import.

![](images/tem_tecnai_icon_on.png)

![](images/admin_instrutable.png)

## Applications

Applications define how nodes are linked together in order to form a specialized Leginon application or program. Because Leginon uses a nodal or modular archetecture, multiple applications can be created by linking together nodes in different fashions suitable for the current experiment. Several default Leginon applications are distributed with the release. This section enables the Leginon user to import and export applications.

## Import Applications online

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Applications.

![](images/application_on.png)

-   Enter the name of the Leginon application XML file. These are files in a subdirectory of your leginon installation called "applications" starting from Leginon v1.3.

![](images/admin_apptable.png)

-   Select the name of the "To" Host the application will be imported to.


-   Click Import.

## Export Applications online

## to another Host

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Applications.


-   Select the name of the "From" Host.


-   Select the name of the Leginon application.


-   Select the "To" Host.


-   Click "Export"

## to a Leginon application XML file

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Applications.


-   Select the name of the "From" Host.


-   Select the name of the Leginon application.


-   Keep "Export to XML format" enabled.


-   Enable "Save as"


-   Click Export

## to the screen in XML format

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Applications.


-   Select the name of the "From" Host.


-   Select the name of the Leginon application.


-   Keep "Export to XML format" enabled.


-   Click Export

## to the screen in "easy-to-read" format

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Applications.


-   Select the name of the "From" Host.


-   Select the name of the Leginon application.


-   Select View


-   Click Export

It should contain tables of Application Data, NodeSpec Data, and likely BindingSpec Data.

## Calibrations

Good calibrations are absolutely essential to running Leginon. They can also be very time consuming. As a way of rudimentarily starting up without calibrating the current instrument specifically or perhaps to revert to a previously saved calibration, this import/export calibration tool can be quite useful.

## Import Calibrations

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Calibrations.


-   Enter the name of the Leginon calibration XML file.


-   Select the name of the To Host the calibrations will be imported to.


-   Click Import.

## Export Calibrations

## to another Host

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Calibrations.


-   Select the name of the "From" Host and desired Instrument.


-   Select the names of the calibrations to export.


-   Select the "To" Host and desired Instrument.


-   Click Export

## to a Leginon application XML file

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Calibrations.


-   Select the name of the "From" Host and desired Instrument.


-   Select the names of the calibrations to export.


-   Keep "Export to XML format" enabled.


-   Enable "Save as"


-   Click Export

## to the screen in XML format

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Calibrations.


-   Select the name of the "From" Host and desired Instrument.


-   Select the names of the calibrations to export.


-   Keep "Export to XML format" enabled.


-   Click Export

## to the screen in "easy-to-read" format

-   Open a web browser. Go to http://localhost/myamiweb/admin.php


-   Click on Calibrations.


-   Select the name of the "From" Host and desired Instrument.


-   Select the names of the calibrations to export.


-   Select View


-   Click Export

![](images/calibration_on.png)

![](images/admin_caltable.png)

## Goniometer

The goniometer movement must be modeled for finer movements. Leginon calibrates this movement through the Gon Modeler node. Through this feature, the models for these movements can be graphically seen.

## View the Goniometer Model

-   Open a web browser. Go to http://yourhost/dbem/admin.php


-   Click on Goniometer


-   Select a model to display.


-   Click view.

![](images/goniometer_on.png)

![](images/admin_gontable.png)
