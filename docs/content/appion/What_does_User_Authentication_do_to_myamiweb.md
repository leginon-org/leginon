Purpose of optional user authentication system in combination of Project Management in the Leginon/Appion Database Tools on the webserver is to provide different levels of user privileges at institution where the webserver is available to all. In addition, by assigning project owners, users in the lower privileged group will not see projects from others. It makes finding an experiment session easier once data are accumulated. Enabling of the system is not required, but is recommended if the web server can be accessed freely outside the intended group. **Once enabled, no myamiweb pages can be accessed without login at its required privilege**.

Four levels of group privileges are included with the complete installation of Leginon/Appion 2.0, and four user groups are created by default to reflect them, respectively

  ------------------------------------------------------------------- --------------------
  privilege level                                                     default group name
  All at administration level                                         administrators
  View all but administrate owned                                     power users
  Administrate/view only owned projects and view shared experiments   users
  View owned projects and shared experiments                          guests
  ------------------------------------------------------------------- --------------------

These four default groups would not appear in the database of a system upgraded from earlier version to 2.0. During the upgrading, the group in which the "administrator" user is in is assigned to "All at administration level" privilege. All other groups are assigned to "Administrate/view only owned projects and view shared experiments" privilege. This can be changed [after the database upgrade is completed](/appion/leginonPreparation_before_Using_v20_Routinely).

Rule examples:

-   only administrators can create projects, move a user between groups, and create a grid tray shared by all users.


-   As a project owner and in the group "users", a person can add another user to his/her owned group to share the data and process the data together with appion if the other has at least the same level of privilege.

To enable or disable user authentication, run the setup wizard at http://YOUR_SERVER/myamiweb/setup.

_

Related Topics:

[Install the Web Interface](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface)
[Leginon upgrade instruction](/appion/leginonHow_to_Update_from_v16_Linux)
[User Guide on User Authentication/Management](/appion/Appion_Manual/Appion_User_Guide/Appion_and_Leginon_Database_Tools/User_Management)

_
