You can get tem and camera simulator from manufactures and setup virtual machines for development.

I set up 2 virtual machines on my MacBook with VMware and can run all the tcp transporter tests and image acquisition using a few specific settings as follow:

On the mac, find out the hostname known by python socket module. In python command line

    import socket
    socket.gethostname()


My mac is called anchi3.local

For each virtual machine

1.  Open Network Adopter settings through menu VMware Fusion/Virtual Machine\Network Adopter\Network Adopter Settings...
2.  Select to use "Private to my Mac" and activate "Connect Network Adaptor" if not already chosen.
3.  Follow [instruction for adding IP address and matching hostname in your host file](/leginon/Leginon_Manual/Complete_Installation/Installation_on_the_instrument_computers/Windows_Installation_All#Add-the-IP-address-and-matching-hostname-of-the-microscope-and-digital-camera-computer-in-your-host-file-on-the-main-Leginon-computer,-and-vice-versa.) to make all parties on this private network know each other by hostname
4.   Note: the virtual machine knows the real machine as "anchi3", not "anchi3.local"*. You should associate both names with the private network IP (127.xx.xx.1)

On the mac, the /etc/hosts should include assignment to each virtual machine as well as its own private network IP. I have

    127.xx.xx.128 virtual1
    127.xx.xx.129 virtual2
    127.xx.xx.1 anchi3 anchi3.local
