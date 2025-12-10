
A specific file tree structure has been assumed in Appion/Leginon. Here is a description of it:

## Head path

Leginon and Appion are saved under the same head directory, and it is assumed to have one.
For example **/your_file_server_mount_point/whatever** is the head directory.
You can have is shorter such as **/whatever**, but not just /

## User not identified in the path

1. Leginon default image path is defined in [leginon.cfg](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Configure_leginoncfg). The acceptable form is **/your_file_server_mount_point/whatever/leginon**. The images are saved by sessionname under subdirectory of this directory in a form such as
**/your_file_server_mount_point/whatever/leginon/sessionname/rawdata/**.
2. Leginon DD movie frames path is defined relative to the Leginon image path once it is set for the session. In the case of the above example, the resulting path is
**/your_file_server_mount_point/whatever/frames/sessionname/rawdata/**.
3. Appion processing is default under appion directory parrallel to leginon directory, i.e., /your_file_server_mount_point/whatever/appion. This relationship is hard-coded until v2.2 release. In later releases, the parent directory can be set differently in the webserver myamiweb config.php. The processing are divided by sessionname and then processingtype and then runname of the process. Therefore, your processing results are saved in the following default appion path: **/your_file_server_mount_point/whatever/appion/sessionname/processing_type/runname/**

## User identified in the path in a subdirectory of leginon

It is possible to add one more layer below leginon directory to identify users by their username or groupname. In this case;

1. Leginon default image path can be made to be **/your_file_server_mount_point/whatever/leginon/username/sessionname/rawdata**.
2. frame directory is then **/your_file_server_mount_point/whatever/frames/username/sessionname/rawdata**.
3. In webserver myamiweb/config.php. **APPION_PARENT_ADDITION** should be set to 1. This will preserve username subdivision and give default appion path of **/your_file_server_mount_point/whatever/appion/username/sessionname/processing_type/runname/**

## User identified in the path in a parent directory of leginon

It is possible to add one more layer above leginon directory to identify users by their username or groupname. In this case;

1. Leginon default image path can be made to be **/your_file_server_mount_point/whatever/username/leginon/sessionname/rawdata**.
2. frame directory is then **/your_file_server_mount_point/whatever/username/frames/username/sessionname/rawdata**.
3. In webserver myamiweb/config.php. **APPION_PARENT_REPLACEMENT** should be set to ---1. This will preserve username parent division and give default appion path of **/your_file_server_mount_point/whatever/username/appion/sessionname/processing_type/runname/**

## Permission

The following permission rule is required for multi-unix-user usage of Leginon/Appion:

For Leginon:

1. The web server redux running user need to have read permission to all images in the rawdata directories in order to display them in the viewer.
2. all users need to have permission to create directory at the level of sessionname. For standard structure, this means **/your_file_server_mount_point/whatever/leginon**.
3. If DD frames are saved and managed by Leginon, the user running the frame rawtransfer.py (typically root) need to have permission to create directory in **/your_file_server_mount_point/whatever/frames**
4. All users need to have read permission in a leginon rawdata directory that contains reference images. You can specify this through leginon.cfg as
[References]
path: /common_path/leginon_references
5. Users need to have write permission to the session they created, of course.

For Appion:

1. Images uploaded to Appion is considered as a Leginon session. See above for its file tree structure.
2. The web server apache user need to have read permission to processing directories to display the results.
3. All users need to have permission to create directory in **/your_file_server_mount_point/whatever/appion**
4. If more than one user will be processing data in the same session, they all need write permission to the session directory **/your_file_server_mount_point/whatever/appion/sessionname/**



[< Database Server Installation](/appion/Appion_Manual/Complete_Installation/Database_Server_Installation) | [Processing Server Installation >](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation)
