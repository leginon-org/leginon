This is the README file for installing ACE.

I have numbered the commands to distinguish them from text.

Download ace_version_num.tgz

Unzip and untar is using

1) tar -zxvf ace_version_num.tgz

A directory called "ace" would be created

2) cd ace

Start matlab. For example, AMI users can type

3) matlab

MATLAB desktop should start.

Following commands are should be used inside the MATLAB desktop. The commands of
interest to a user are:

a)leginon_ace_gui : Launches the graphical user interface CTF estimation.
b)leginon_ace_correct: Launches the graphical user interface for CTF correction.
c)acedemo: A demo program for non-leginon users for CTF estimation.

The above commands can be executed by typing the above commands in MATLAB command
prompt followed by ENTER. For example

4) leginon_ace_gui

To get help on any of the above commands type:
doc command_name
For example

5) doc leginon_ace_gui

Just typing

6) doc ace

would take you to the main help page of ACE.

Hovering the mouse over buttons and objects on the GUI  also tells their
functionality. To get help on other functions that legion_ace_gui calls ,
just type

6) help function_name

There are other ways to get to the help files also, for example follow the buttons :

Start--> Toolboxes --> ACE

