## Protobuf installation instruction

Google Protobuf is an open source communication library DE use between client and server. For C programs, it is built into the program, so no external library installation is needed. However, for Python/Leginon only, the library will need to be added. A simple way to install this for python use on DE camera computer (Windows) follows:

1.  Download 2.3.0 source zip file as well as the win32.zip binary file
2.  Unzip both packages.
3.  Copy the binary file protoc-2.3.0-win32/proc.exe into protobuf-2.3.0\protobuf-2.3.0\src folder
4.  Go into protobuf\python and run "python setup.py install".

Note: If it attempts to install 0.6c9 version of setuptools and failed to obtain the file, download the ez_setup.py file from setuptools for Windows 7 at https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py You can then replace the one in your protobuf-2.3.0/python folder.
