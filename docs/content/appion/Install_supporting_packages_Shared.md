Using the Required Supporting Packages table below, install any missing prerequisite packages by following the instructions for your specific Linux distribution.

For example, SUSE users can use YaST to install them; RedHat and CentOS users can use `yum`, Debian and Ubuntu uses `apt-get`.

We highly recommend using pre-built binary packages to install the programs. Installing from source can quickly become a nightmare! See also the previous page, [appion:Instructions for installing CentOS on your computer](/appion/appionInstructions_for_installing_CentOS_on_your_computer) for Red Hat based systems.

### Required supporting packages:

  Name:                                         Download site:                             yum package name   SuSE rpm name   Debian 8 package name
  --------------------------------------------- ------------------------------------------ ------------------ --------------- -----------------------
  Python 2.7 or newer                           <http://www.python.org>                    python             python-devel    python
  wxPython 2.5.2.8 or newer                     <http://www.wxpython.org>                  wxPython           python-wxGTK    python-wxgtk3.0
  Python Imaging Library (PIL) fork Pillow *   https://pillow.readthedocs.io/en/stable/   python-pillow      python-pillow   python-pillow
  NumPy 1.0.1 or newer                          <http://numpy.scipy.org/>                  numpy              numpy           python-numpy
  SciPy 0.5.1 (tested, others may work)*       <http://www.scipy.org>                     scipy              python-scipy    python-scipy

PyMySQL:

    pip install PyMySQL==0.10.1


### Appion Only (3.2) > **Note:** See [New support package requirement for 3.2](/appion/New_support_package_requirement_for_32)

### Appion trunk only

> **Note:** See [New support package requirement for 3.3](/appion/Appion_Manual/Upgrade_Instructions/Upgrade_From_30_or_above/New_support_package_requirement_for_33)


For CentOS, see [appion:Download additional Software](/appion/appionDownload_additional_Software) page, if you have trouble finding these packages.

### Scipy/Numpy

#### SUSE specific issues

-   SciPy may not build from source properly on some versions of SuSE due to an incompatible LAPACK package that comes with SuSE. You can get scipy as well as a compatible LAPACK etc. from http://repos.opensuse.org/science (need to specify your SuSE version and machine etc.)
-   See also https://bugzilla.redhat.com/show_bug.cgi?id=489887 regarding LD_LIBRARY_PATH restriction to LAPACK installation.

You can test your numpy and scipy install with their build in test functions:

    python -c 'import numpy; numpy.test(level=1)'
    python -c 'import scipy; scipy.test(level=1)'

Numpy is more stable should be successful. Expect to see lots of errors with scipy.

### Mac OS X 10.5+:

You can successfully install most of these packages on a Mac by downloading DMG files and clicking on the install programs. This is not for novice Mac user. Be warned, wxpython problems on Mac will make your life difficult in using Leginon gui. Don't make your mac the only processing server if it is Leginon that you will use mainly.

1.  First, start by downloading the `Mac OS X Installer Disk Image` (v2.6 recommended) from http://python.org/download/ and install the newer version of python
2.  Download and install numpy and scipy DMG files from http://sourceforge.net/projects/numpy/files/ and http://sourceforge.net/projects/scipy/files/
3.  Download and install wxPython DMG file from http://www.wxpython.org/download.php

Other program need more work:

1.  The Python Imaging Library (PIL) has be compiled from source, which also requires the [Mac OS X Developer tools](http://developer.apple.com/technologies/tools/) to be installed.
