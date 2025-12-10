## Create Leginon Admin and Leginon Client shortcut in Start menu menu under Leginon

This instruction applies to Windows XP.

* Go to C:\Documents and Settings\All Users\Start Menu\Programs\ and create a new
folder named Leginon.

* In another window, go to


C:\Python27\Lib\site-packages\leginon


* Create a shortcut from start-leginon.py as "Leginon Admin" and a shortcut from launcher.py as "Leginon Client".

* Move the two shortcuts into


C:\Documents and Settings\All Users\Start Menu\Programs\Leginon


## Alternatively Create Shortcut on the Desktop of the same.

## Mapping Drives (Optional):

Although we don't recommend it, it is possible to run minimal Leginon directly on the Windows machine, Since the database and web servers are not there, you probably will be saving the images through a Samba server on a network drive also available to the Linux machine. If you do so, you will need to map the network drive. For example, if your Samba server has a hostname your_smbserver, and you have set up a share called [your_share_point] which points to /your_data_path/ and leginon data will be saved under a folder in /your_data_path/leginon/.

-   Start, My Computer


-   Tools menu, Map network drive


-   Use an unmapped drive such as Z:

Enter shared path in Windows format as


\your_smbserver\your_share_point


* Add the drive and the Linux path to leginon.cfg on the Windows machine as


[Drive Mapping]
Z:/your_data_path


* Add image path to leginon.cfg on the Windows machine in Linux format as


[Images]
path:/your_data_path/leginon


## Additional Software (Optional):

TigerVNC (http://tigervnc.org/) --- allows remote access to windows screen. If you get tired of going into the microscope room just to open the column valves.

[< Additional installation specific to the camera](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Installation_on_the_camera_computer) | [Trouble shooting with Python IDLE >](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Trouble_shooting_with_Python_IDLE)
