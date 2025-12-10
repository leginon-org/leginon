The following instructions apply to:

-   Gatan CCD cameras using the pyscope gatan.py module starting with svn r17592
-   FEI cameras (Eagle,Falcon) using the pyscope tia.py module starting with svn r17589

Prior to those revisions, the comarray package was required. You no longer need to install comarray. Instead, you must install comtypes, available here:

http://sourceforge.net/projects/comtypes/files/comtypes/0.6.2/

Be careful not to accidentally download the py3 version. Install it from the exe installer, or unzip the source and install using the setup.py installer. The same package should work with any 2.* version of python.

IMPORTANT: After installing comtypes, you must make one modification to it. The module "safearray.py" that comes with comtypes must be replaced with a modified version that we provide. You can find the custom version of safearray.py in the pyscope package. Please copy this module from pyscope into the installed comtypes folder: C:\Python2*\Lib\site-packages\comtypes. It should replace the safearray.py that is included in comtypes.
