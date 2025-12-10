Numextension is a Python module containing a set of functions Leginon needs to operate on Numpy arrays. Since it is implemented in C rather than in pure Python, the module must be compliled before using. You can avoid compiling yourself by using one of the provided Windows installers for commonly used versions of Python and Numpy. For non-standard or newer versions of Python/Numpy, use the instructions below for doing your own compile.

## Pre-compiled Windows Installers

-   attachment:numextension-git.win-amd64-py3.6.exe
-   attachment:numextension-git.win-amd64-py3.7.exe
-   attachment:numextension-git.win-amd64-py3.8.exe
-   attachment:numextension-git.win-amd64-py3.9.exe
-   attachment:numextension-3.1.0.win-amd64-py3.10.msi

## Compiling Numextension on Windows

### Install Build Tools

Windows versions of Python and Numpy are developed using Microsoft Visual Studio. Extension modules written in C should also be compiled with VS. Luckily you do not have to install a full version of Visual Studio. Compiling a Python extension only requires a minimal set of command line build tools. These tools are documented here:

https://docs.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-160

and can be downloaded from here:

https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019

### Install Python and Numpy you want to compile numextension for

-   You may install multiple versions of python, then use the "py" launcher to select which one to use
-   Download and install Python: https://www.python.org/downloads/windows/
    -   In the optional installation features, it is recommended to select installing "py launcher" so you can easily select which python version to run on the command line
-   Use pip on the command line to install numpy, use specific pip for version of python you are installing in (eg. pip3.8, pip3.9, etc)
    -   As of 2020-11-29, there is a bug in Win 10 (update 2004) that prevents some versions of numpy to work correctly. The bug and workaround is detailed here: https://developercommunity.visualstudio.com/content/problem/1207405/fmod-after-an-update-to-windows-2004-is-causing-a.html
    -   Workaround is to install older version 1.19.3 version of numpy instead of 1.19.4:
        -   pip3.8 uninstall numpy (if you already have numpy installed)
        -   pip3.8 install numpy==1.19.3

### Compile numextension in a VS native tools command prompt:

-   Search and launch this from start menu: "x64 Native Tools Command Prompt for VS 2019"
-   cd to the numextension directory
-   compile and build a windows installer for your specific Python version.
    -   py --3.8 setup.py bdist_wininst
-   The new windows installer will be found in the numextension/dist folder

## MacOS and some linux system python3 compilation

If you get this error:
<pre>
  File "/opt/applications/myami/3.6/lib64/python3.9/site-packages/numextension/__init__.py", line 17, in <module>
    import _numextension
ModuleNotFoundError: No module named '_numextension'
</pre>

Then it is looking for _numextension.so. (instead numextension.cpython-39-x86_64-linux-gnu.so is created.)

You can resolve this error by moving numextension.cpython-39-x86_64-linux-gnu.so from your installed location such as /lib/python3.9/site-packages/numextension-1.0.0-cpython-39-x86_64-linux-gnu.egg to /opt/applications/myami/3.6/lib64/python3.9/site-packages

## Testing numextension

-   Each function of numextension can be tested using numtest.py, which can be found in directory numextension/test/ (In Git, not in the installed numextension)
-   This was in numext3 branch but is now merged into myami-python3 branch.
-   numtest.py requires pyami, and therefore a minimal set of modules from pyami have been converted to python 3 in the same branch
-   Conversion of pyami from py2 to py3 includes the use of the "future" and "past" modules. To use this minimally converted pyami, you will also need to install the "future" package using pip.
-   numextension/test/ also contains a reference input image and a reference set of data for the tests in numref.py and several other MRC images.
-   Running numtest.py will use the reference images and data within numref.py to determine if each test passes
-   It will also write out a set of MRC images, which are the output from testing the numextension functions. These are compared against the reference images. These test output images are prefixed with "test_..."