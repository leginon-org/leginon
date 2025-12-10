
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
