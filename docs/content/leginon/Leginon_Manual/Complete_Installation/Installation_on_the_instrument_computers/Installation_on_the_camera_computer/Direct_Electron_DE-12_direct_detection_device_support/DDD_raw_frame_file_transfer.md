## Introduction:

Due to the limited disk space on the camera host computer, we wish to transfer the raw frame data to a location with more storage space. The following assumes the camera host is a Windows system and the destination is a linux system. For best performance, the linux system should be directly attached to the destination storage rather than over a network. The "rawtransfer.py" script will run continuously in the background on the linux system, independent from Leginon. It will periodically check the Leginon database to see if any new raw frames have been acquired by Leginon, then pull them over the network from the camera host.

In addition, the script changes the directory naming (DE and Falcon) or stack file naming (K2 Summit) to reflect the integrated image filename transmitted to Leginon. Therefore, even if you have network it so that the frames are directly saved to the file server, you should make modification of rawtransfer.py and use it to do this filename synchronization.

## Initial setup of your systems:

**Camera host (Windows)**: the folder where your raw frames are stored must be configured as a shared folder (without a password in our example). Remember the share name, as you will need it when mounting from linux. For more information about sharing on Windows 7, see http://windows.microsoft.com/en-us/windows/share-files-with-someone#1TC=windows-7

**Destination host (Linux)**: The samba-client package must be installed in order to mount the shared Windows folder

## Mount the shared folder

From the linux host, mount the shared folder on the camera host with SAMBA. For example, the windows system host name is "decamera" and the shared folder is "D:\RawFrames\DE12\", but has a share name of "DE12". The mount command would be:

    mount //decamera/DE12 /example_mount_point

(replace example_mount_point with a directory you have created for this purpose).

## Create the destination folder to store the frames organizes by Leginon sessions.

See [File Server Setup Considerations](/leginon/Leginon_Manual/Complete_Installation/File_Server_Setup_Considerations) for the location saved in the database when the session was started.

As an example, leginon.cfg specified image path to be /your_file_server_mount_point/whatever/frames/sessionname/rawdata/. Your frame path for the session is then located at /your_file_server_mount_point/whatever/frames/sessionname/rawdata/. The folder you need to create now is, therefore, /your_file_server_mount_point/whatever/frames.

## Start rawtransfer script in the background

The script "rawtransfer.py" is provided in the leginon package, usually installed in your python site-packages folder (referred to as PYTHONSITEPKG below). In the future, this script will be wrapped up in a proper init script such as you would find in /etc/init.d. That would allow for automatically starting it when the system boots, but for now you must launch it manually.

**myami-3.0 and up**
You need to pass in several options

      --method=METHOD       method to transfer, e.g. --method=mv or --method=rsync
      --source_path=PATH    Mounted parent path to transfer, e.g. --source_path=/mnt/ddframes
      --camera_host=CAMERA_HOST   Camera computer hostname in leginondb, e.g. --camera_host=gatank2
      --destination_head=PATH  Specific head destination frame path to transfer if
                            multiple frame transfer is run for one source to frame paths not all mounted on the same computer, e.g. --destination_head=/data1

For example,

    nohup $PYTHONSITEPKG/leginon/rawtransfer.py --method=rsync --source_path=/example_mount_point --camera_host=scope1cam1 --destination_head=/your_file_server_mount_point/whatever > rawtransfer.log

-   mv method is used when the frame files are saved directly onto network drive. No transfer is needed. However, since the filename is only timestamped, this script will change the filenames and organize them by sessions.
-   In this version, files are saved under frames directory and organized by session below. With the destination_head in the example, the resulting frames.st file will be in
        /your_file_server_mount_point/whatever/frames/your_session/rawdata/image_name.st
-   destination_head/frames directory should exist and writable before running this.
-   If you have another frame-saving camera on scop2cam1 then you start another on with different -source_path and ---camera_host values.

The script is currently set up to check for new frames every 30 seconds. If it finds new files, it will check the database to see if they are connected to a Leginon image. If it is from Leginon, then it will rsync or move the folder to the rawdata folder for that session. The name of the folder will be something like: 11nov28_00001sq_00001_hl_00001_en.frames (based on the same name as the Leginon mrc image). Then it will remove the original folder. It looks like it can copy one frame per second, but this could vary depending on network traffic. Any frames folders found that are not connected to a Leginon image are not transferred and not removed, so you may want to periodically clean up those extra frames.
