Before we start, make sure to [set up an RPM build environment under CentOS](http://wiki.centos.org/HowTos/SetupRpmBuildEnvironment). Notice that [rpmbuild is building in /root/rpmbuild](http://help.directadmin.com/item.php?id=381) on CentOS 6.

We use attachment:myami-2.2.spec to build rpm package for myami-2.2.

    Name:           myami
    Version:        2.2
    Release:        757
    Source0:        %{name}-%{version}.tar.gz
    License:        Apache
    Summary:        Data collection and procession processing tools for EM
    Vendor:         NRAMM/Scripps Research Institute AMI Group
    URL:            http://nramm.scripps.edu
    Group:          Applications/Engineering and Scientific
    BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
    AutoReq:        0
    Prefix:     /opt/%{name}-%{version}
    ...


The [Prefix](http://www.rpm.org/max-rpm/s1-rpm-reloc-prefix-tag.html) tag here shows that, by default, rpm will install our files under /opt/myami-2.2.

For our automated build procedure we use attachment:buildMyamiSnapshot-2.2.py. Line 6 in buildMyamiSnapshot-2.2.py defines where myami-2.2.spec is stored:

    specFile = '/root/rpmbuild/SPECS/myami-2.2.spec'


In other words, we need to store attached myami-2.2.spec under /root/rpmbuild/SPECS. Line 7 in buildMyamiSnapshot-2.2.py defines workingDir as:

    workingDir = '/root/src/myami-2.2'


This workingDir where we need to checkout myami-2.2 files to:

    cd /root/src
    svn co http://emg.nysbc.org/svn/myami/branches/myami-2.2


In order to run buildMyamiSnapshot-2.2.py nightly, add the following to /var/spool/cron/root:

    55 22 * * * /root/bin/buildMyamiSnapshot-2.2.py

# Summary

Attached myami-2.2.spec and buildMyamiSnapshot-2.2.py are used get the latest myami-2.2 files from SVN, build and create rpm package, and install myami-2.2 under /opt/myami-2.2.
