## This only applies to 2.2 version. For trunk or newer installation, comtypes replaces this. See [Installing comtypes](/leginon/Installing_comtypes)

We are still in the process of adapting the comarray package to work with the FEI Eagle cameras. The pre-packaged comarray EXE installer that we provide here will not work, so you will need to download comarray from our SVN repository and do a manual installation of the python module to your python site-packages. Here is the procedure:

Check out comarray to your local sandbox on a linux system like this:

     svn co http://emg.nysbc.org/svn/myami/trunk/comarray


Then copy it to your Windows system that hosts the camera. Or just check it out directly to the Windows system using a Windows SVN client.

Now browse through the files in your new comarray sandbox. You will find a folder "py2.5". In there you will find a few files including:

     __init__.py
     NumpySafeArraySlow.py
     NumpySafeArray.pyd
     NumpySafeArrayTIA.pyd
     setup.py

Make a new folder C:\Python25\Lib\site-packages\comarray

Copy "*init*.py" and "NumpySafeArrayTIA.pyd" to the new site-packages/comarray folder.

In the site-packages/comarray folder, rename NumpySafeArrayTIA.pyd to NumpySafeArray.pyd
