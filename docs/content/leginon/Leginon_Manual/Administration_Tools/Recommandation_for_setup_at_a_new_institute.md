
## User Groups

- Administrators : See and do everything

- Power Users : See everything but not to modify
- Users : See and process only projects they own or a session being shared by someone who owns the project.

## Leginon/Appion Administrator

The user with username "administrator" is a special user in Leginon/Appion. It belongs to the administrator group with highest level of privileges if the login is enabled at the web server. For legion operation, once the setting preferences in a node that shares the same class and alias are defined by the administrator, all newly created users get these settings when they launch the node until they make changes themselves. This allows a faster setup per database (institute) for the beginners. The web server setup wizard should have guided you to create this user.

If you are the Leginon guru at your institute, you may want to start Leginon as the administrator and modify its node settings once you have figured out the appropriate values at your institute so that you won't have to check and modify them for every new users.

## Guru

As your institute guru, you will want to have a login that you can run experiments without modifying the default. Therefore, you should create a user for yourself. **Put it in "Administrators" group** so you can see and manage everything.

## Regular users :

A Leginon?Appion user set in the adminstration tool defines his/her own Leginon preferences once changed from the "adminstrator" user default above. The user profile is also used for the login feature in the web imageviewers and Appion interface. It is important to know that this user is not related to the computer login user. Therefore, Follow the steps outlined in [Set up for a new regular user](/leginon/Leginon_Manual/Administration_Tools/Set_up_for_a_new_regular_user) section to register a new user. **These users should be put in "Users" group**.



[Steps involved in the installation >](/leginon/Leginon_Manual/Administration_Tools/Steps_involved_in_the_installation)
