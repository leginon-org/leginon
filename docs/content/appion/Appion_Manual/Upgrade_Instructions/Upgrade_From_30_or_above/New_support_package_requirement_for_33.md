  Name:   Download site:   yum package name   SuSE rpm name   Debian 8 package name
  ------- ---------------- ------------------ --------------- -----------------------
  h5py                     h5py               python-h5py     python-h5py

-   disable the archive rpmforge before reinstall if seeing error on import:
        ImportError: libhdf5.so.6: cannot open shared object file: No such file or directory

    
    See https://www.centos.org/forums/viewtopic.php?t=46181
    and
    http://kbfaq.blogspot.com/2011/08/installing-rpmforge-repository.html
