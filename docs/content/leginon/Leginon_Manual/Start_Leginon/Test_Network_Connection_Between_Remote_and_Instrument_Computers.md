By far the biggest installation problem comes from network connection is block at the microscope/camera computer from the remote computer where the main Leginon program is run. Here is a test to do before trying to start leginon operation at the remote computer. Leginon bulletin board has a thread that has [various problems and solutions](http://emg.nysbc.org/redmine/boards/6/topics/3) from users.

## Start a Test Launcher on the Microscope Computer

# scope> go to the location where Leginon is installed, generally


C:\Python27\Lib\site-packages\Leginon


1.  scope> double click on test1.py. You should see something like this:
        INFO localtransport server created at location {'instance': <localtransport.Server object at 0x40e614cc>}
        INFO tcptransport server created at location {'hostname': 'myscope', 'port': 49152}
        INFO <class 'event.SetManagerEvent'> binding added for destination myscope, method <function printData at 0x40e63c34>
        ACCEPTING CONNECTIONS AT:  myscope:49152
        hit enter to kill

    
    **If the line before last says ACCEPTING CONNECTIONS ...., you have an opened port on this host.
     
2.  Write down the name of the hose, in this case "myscope", and the opened port, in this case "49152", and proceed to try to connect to that computer from the remote compute in the next step.

## Attempt Connection from the Remote Computer

# remote linux computer> go to the location where Leginon is installed, type the following to find the location:


start-leginon.py -v


1.  remote linux computer> start the 2nd test script with the host name of the microscope computer and its open port
        remote linux computer/Leginon>test2.py myscope 49152

    
    You should see something like this:
        INFO localtransport server created at location {'instance': <localtransport.Server object at 0x2b08e0d43810>}
        INFO tcptransport server created at location {'hostname': 'myremote', 'port': 49152}
        ACCEPTING CONNECTIONS AT:  myremote:49152
        INFO <class 'event.NodeAvailableEvent'> binding added for destination myremote, method <function printData at 0x2b08e0d51c80>
        CONNECTING TO:  myscope:49154
        WARNING localtransport client add failed
        INFO tcptransport client added
        INFO server location set to to {'TCP transport': {'hostname': 'myscope', 'port': 49154}}
        hit enter to kill

        INFO handling threaded
        INFO inserted in queue (class NodeAvailableEvent)
        INFO <class 'event.NodeAvailableEvent'> handling destination defcon1, method <function printData at 0x2b08e0d51c80>
        REMOTE CLIENT RESPONDED:  myscope:49154

If you get the last line "REMOTE CLIENT RESPONDED" with correct hostname and port, the
connection is fine. You can go to next section to test Leginon run on the remote
computer.

You can ignore the following error message print out in test1.py on the microscope PC when you exit it.

    tcptransport.TransportError: No route to host

## Array Transport tests

There is another pair of tests in leginon: **test1_array_transport.py** and **test2_array_transport.py** that, in addition to the connection test, also send through this connection a few simulated image array. This allows a test of the transfer speed and of the continuing connection.

They run in the same way as the above test.py and test2.py. The output is longer. On the window for test1_array_transport.py output, you should find timing of how long it takes to send 32uint 4096x4096 array (=0.5 gigabit), like this:

    Event Sent Time (sec) 0.811000108719

The sent time depends on your network speed.

Prior to that line of timing, it would say that it inserted into queue what it needs to sent etc and the location it is sending to, like this:

    INFO inserted in queue <ckass SetManagerEvent> handling threaded
    INFO leginon.tcptransport client added
    INFO server location set to {'TCP transport':{'hostname': your_test2_hostname, 'port': the port_test2_opened}}
    INFO <class 'leginon.event.ArrayPassingEvent'> handling destination anchi3.nimgs.com, method <function printData at 0x103f0eb18>

On the window for test2_array_transport.py output, you should get, before the line "hit enter to kill":

    INFO inserted in queue (class ArrayPassingEvent)
     INFO handling threaded
    INFO <class 'leginon.event.ArrayPassingEvent'> handling destination anchi3.nimgs.com, method <function printData at 0x103f0eb18>
    got array (4096, 4096)

This message will repeat as many times as the number of arrays being sent from test1_array_transport.py

If the basic test1.py test2.py pair in the previous section passes but not this. It means that your network connection has trouble keeping the connection alive after each transmission.

## Problem solving tips

-   See Leginon bulletin board thread on [network problem, Leginon not seeing tecnai host](http://emg.nysbc.org/redmine/boards/6/topics/3)

## Check if the hostname case matches

Python is case-sensitive. We have seen it rejects the host because of it. If using host file to identify the host, it is best to match the case as found from leginon/test1.py

## Most likely reason for the failure of the test: FIREWALL

-   The easiest solution is have the involving computers inside the same firewall.

* Alternatively, you can

1.  add python to firewall application exception OR
2.  open [specific ports for Leginon system](/leginon/Leginon_Manual/Complete_Installation/Network_Configuration/Ports_used_by_Leginon)

The latter is described in the Leginon bulletin board thread on [network problem, Leginon not seeing tecnai host](http://emg.nysbc.org/redmine/boards/6/topics/3)

## Another possible reason for the failure of the test: hostname-ip address mismatch

For leginon to communicate through socket, it needs to know the hostname of itself and the other computer it is connected to in both ways. The hostname also need to map properly to the IP address the partner understand as.

If you are on a dynamically assigned domain name system (DNS), this should all be taken care of. However, since the local hosts file overwrites the DNS assignment, you should check if you have a mismatch if you do have problem.

You should therefore check if you have [added hosts](/leginon/Add_host) to the right files on both sides of the connection.

To confirm what python thinks the hosname is on its own computer, run the following in python command line:

    import socket
    socket.gethostname()

You can also get the IP address with this python command after importing socket like above

    socket.gethostbyname(socket.gethostname())

You should also check what one computer think the another's ip address is through socket connection once you know the hostname for the other computer

    socket.gethostbyname('hostname_of_the_other_computer')

### What if the host IP address obtained from socket.gethostbyname on a computer with multiple network card is not the network that connects to other hosts involved in Leginon

### Solution 1: **create mapping on the computers that need communication with the needed pairing**.

This works if the problem is on your leginon linux box.

For example, your leginon linux box has two network connections, one local one toward your scope and camera (192.168.10.30, for example), and one toward your university internet(123.456.78,9). Its hostname "leginonmain.my.u.edu" is default to the university network 123.456.78.9.

If there is not a mapping of

192.168.10.30 leginonmain.my.u.edu

in the scope/camera Windows 7 computer C:\WINDOWS\system32\drivers\etc\hosts, the communication will fail.

### Solution 2: use customized name mapping using pyami.cfg on top of Solution 1


Feature #4686 was created to handle the case that the computer host default its IP mapping to a card not the one to connect to leginon need.

## [create the require ip mappings](/leginon/Add_host) in/etc/hosts (or on Winodows: C:\WINDOWS\system32\drivers\etc\hosts)

## Create specific host-ip pairing in pyami.cfg

1. The template is myami/pyami/pyami.cfg.template in your myami git clone. Copy the template file to your global myami configuration directory. You should know where that is thru [this instruction](/leginon/Locate_global_config_directory_on_Windows)
2. find out the name and ip addresses of the hosts that this computer needs to connect to.
3. rename the copy as **pyami.cfg**
4. edit pyami.cfg according to the mappings

[my ip map]
my-k3-computer: 192.168.0.1

[other ip map]
my-microscop-computer: 192.168.0.2
my-leginon-computer: 192.168.0.3
my-database-server: 192.168.0.4

## Testing

If you have done either python setup.py installation or PYTHONPATH mapping to the myami directories, you should be able to test.

### On Windows, double click your_myami_clone\pyami\mysocket.py

### On Linux, type in terminal

cd your_myami_clone/pyami
python mysocket.py

If the host ip mapping are correct, you should get [OK] in the tests.

my-k3-computer ip mapping [OK]
my-microscope-computer ip mapping [OK]
my-leginon-computer ip mapping [OK]
my-database-server ip mapping [OK]


### Solution 3: reorder the network connections. We had to do this once.

You may need to [reorder the network connections](/leginon/Leginon_Manual/Start_Leginon/Test_Network_Connection_Between_Remote_and_Instrument_Computers/Reorder_the_network_connections) so that the appropriate network is the first to access.

[< Test Leginon on the Computer Controlling the Microscope](/leginon/Leginon_Manual/Start_Leginon/Test_Leginon_on_the_Computer_Controlling_the_Microscope) | [Run Leginon Client on the Instrument Computers >](/leginon/Leginon_Manual/Start_Leginon/Run_Leginon_Client_on_the_Instrument_Computers)
