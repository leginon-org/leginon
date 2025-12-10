### Refused socket connection for SERIALEMCCD_PORT

If an error of "No connection could be made because the target machine actively refused it" comes up in the above test, it could be one of the two reasons:

1.  blocked by firewall
2.  blocked by a still active broken attempt
3.  blocked by an unrelated process after system upgrade by Gatan or some automated process

#### Blocked by Firewall

You should add this to [ports used by Leginon](/leginon/Leginon_Manual/Complete_Installation/Network_Configuration/Ports_used_by_Leginon) to be added to firewall exception port list if leaving the firewall on.

#### Blocked by a still active broken attempt

You can check active tcp port with Windows command

    netstat

-   In some case, you will find SERIALEMCCD or similar listed in Windows Task Manager Processing list. If so, and that process remains after Digital Micrograph is closed, you can terminate it from Task Manager.
-   CurrPorts is a program that can be used to check and close socket tcp connection with gui.

#### Blocked by an unrelated process

After a general software upgrade, it is possible that the upgraded software decided that this is the port it needs and block our connection to the port. The ports after 49153 is consider free ports for any program to use. Therefore, the only way for us to solve this problem is to move to another unused port. Use CurrPorts to find an unused port and assign it should resolve the problem.
