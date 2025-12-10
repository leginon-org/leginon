> **Note:** See external reference `appion:Configure leginoncfg Shared`

This serves as the global leginon configuration.

## Individual User leginon.cfg

For individual Leginon users, the above file can be copied to their home directory and the following added once they have registered as a Leginon user. This extra configuration will allow individual user to skip the step of selecting his/her name from the user list.

    [User]
    fullname: your_firstname your_lastname

    [Project]
    default: your_project_name

-   Important: The name should be typed exactly as registered with firstname followed by lastname. Project name should also be an exact match.
    For example, you entered John as firstname and Doe as lastname during registration, you should enter "John Doe" for fullname, not "Doe, John" nor "john doe"

[< Install Appion/Leginon Packages](/leginon/Install_Appion_Packages) | [Configure sinedon.cfg >](/leginon/Leginon_Manual/Complete_Installation/Processing_Server_Installation/Configure_sinedoncfg)
