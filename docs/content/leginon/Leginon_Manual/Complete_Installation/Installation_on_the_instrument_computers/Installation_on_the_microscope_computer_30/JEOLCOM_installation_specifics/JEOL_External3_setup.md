JEOL's TEM Server and COM interface can be connected through TEMExternal3 program. It is installed on the Client side. In the case of using the COM on JEM scope PC, it means you need to have it on that same computer. If it is available, you will find TEMExtReg.exe at C:\Program Files\JEOL

## Find the external network IP address for the computer.

1.  Click "Run..." from **Start menu**
2.  Open "cmd" in its dialog. This will open *Command Prompt"
3.  Type ipconfig to list the network configuration on the computer.
4.  Look for the IP address assigned to external subnet. It is likely started with "172.17.41"

## Find the socket numbers TEM server is connected to.

1.  Right-Click on the TEM server icon in the notification area or the Taskbar (right-bottom of the display ) ![](images/JeolTEM_Server.png)
2.  Write down "Request Port" number and "Notify Port" number

### Configure TEMExternal3

1.  Open TemExtReg.exe
2.  Assign the IP address to that of the external subnet IP
3.  Assign the two port numbers according to those used by the TEM Server with TEMExternal Normal Port assigned to TEM Server Request Port.
4.  Close TemExtReg.exe by clicking OK
