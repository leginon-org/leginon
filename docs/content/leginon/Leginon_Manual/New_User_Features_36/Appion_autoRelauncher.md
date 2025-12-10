This is a feature to repeat the array of appion scripts and their most recent parameters from an old session to apply to the new session.

For example, frame alignment was run on en preset images of an old session 22mar01a, and ctffind4 was run on the en-a preset image generated from the output of the frame alignment. Once a new session 22mar02a is started, we want to launch 2 parallel frame alignment runs with the same parameters on gpuid 1 and 2. And then run 4 instances of ctffind4 on the same host named appion_server on 22mar02a. We will setup:

1. your_appion_wrapper createAutoHost.py

This interactive program will allow you to setup the configuration for the host you run this from. This only needs to be set once if you don't plan to change it.

    running autohost creation on appion_server
    hostname (as str) = appion_server
    appion_wrapper (as str) = your_appion_wrapper
    ddalign_gpus (as list) = [1,2]
    loop_max (as int) = 4

2. Testing autoRelauncher

    your_appion_wrapper autoRelauncher.py --old-session=22mar01a --new-session=22mar02a --testing


This generate the appion scripts it will run. You can check session name, sessionid, gpuid etc that you typically have to change when relaunch manually.

3. Run autoRelauncher

Remove ---testing flag makes it follow the sequence and run these scripts. There are jobtype dependency coded in autoRelauncher.py so that ctffind script will not launch before an image with en-a preset exists.

    your_appion_wrapper autoRelauncher.py --old-session=22mar01a --new-session=22mar02a
