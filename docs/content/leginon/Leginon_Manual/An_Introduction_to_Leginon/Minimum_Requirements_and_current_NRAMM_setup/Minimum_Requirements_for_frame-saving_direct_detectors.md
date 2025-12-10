This configuration has a strong hardware. If frame and any other post-collection processing will be done else where, this can be reduced.

## Using gpu-based frame alignment:

A good gpu is needed for frame alignment using the program described in Li et. al. (2013) Nat. Method vol. 10 pp584-590 and variants of it.
If real-time speed is desired, parallel processing on multiple hosts may be needed.

Here is an example that we designed as a back up for our typically distributed system. Good for a few days of data collection of Krios/K2 combination.

- 4U 4GPU server - https://www.supermicro.com/products/system/4U/7049/SYS-7049GP-TRT.cfm

- Dual 2.1GHz 8-core CPUs (16 cores total can run database, webserver, leginon, and Appion pre-processing and very minimal post-processing)

- 128 Gb RAM

- 1 Tb SSD scratch space

- GTX 1050 GPU for graphical display.

- Two GTX 1070 GPU cards (will support real-time frame alignment in counted mode)

- 12 Tb of storage in RAID configuration (will support 3-4 days of data collection)
- 10GB network card to support direct transfer from K2 camera and connection to the scope.

To expand from this:

-   Add more storage space or connect to a network storage solution.
-   Add more gpus or have a over-flow frame processing computer to share.

## Recommendation:

Have one primary frame processing computer per direct detector to be used by the person currently using the scope. And an over-flow frame processing computer to share among scopes and users not able to finish during their session. Our experience is that primary frame processing computer can not keep up with super-resolution data collection if binning is not applied ahead of the time. The shared gpu can also be used for gCTF, gAutomatch and other light-weight gpu programs. Counted mode movies can be processed fast enough with just primary frame processing computer.

## For CPU programs that do frame alignment:

A 12 core-computer with Torque scheduler can be used for DE-20 frame alignment. The rest can be used for Leginon data collection if needed. We have not tried it, though.
