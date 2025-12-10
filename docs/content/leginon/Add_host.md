## Add the IP address and matching hostname of the microscope and digital camera computer in your host file on the main Leginon computer, and vice versa.

### Find out what python thinks the hostname is with python command line. REPEAT this both on Linux and Windows PC

Run the following in python command line:

    import socket
    socket.gethostname()

### Find out the ip address associated with the hostname

Run the following in python command line:

    import socket
    socket.gethostbyname('your_host_name')

### Modify your "hosts" file on the linux Leginon computer to include the instrument hosts if the latter is not already mapped by your domain name server

-   On Linux, this "hosts" file is at
    > /etc/hosts

Example of a "hosts" file:

    192.000.1.222   instrument_host_name.domain_name instrument_short_host_name

### Use shorter linux hostname if desired

If you'd like to shorten your linux hostname recognized by socket without the domain name, you may do so as root

    hostname your_shorter_hostname

and also add that to the /etc/hosts as an alternative name

    192.000.1.333   long_host_name.domain_name your_shorter_hostname

You will need to restart networking to make it persistent.

    /etc/init.d/network restart

Test the change by finding the ip address with the hostname as in the above section.

### The Linux main Leginon computer also needs to identify itself by its hostname registered on the instrument Windows computer.

-   On Window XP and WIndows 7 this host file is
    > C:\WINDOWS\system32\drivers\etc\hosts


-   On Window NT, this host file is
    > C:\WINNT\system32\drivers\etc\hosts
