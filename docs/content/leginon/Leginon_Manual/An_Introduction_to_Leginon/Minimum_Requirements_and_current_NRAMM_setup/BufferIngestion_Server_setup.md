NRAMM/SEMC uses a redundant system that keeps pre-processing (frame alignment and ctf estimation) independent between each Krios. The buffer server also has a large enough storage to hold two weeks to a month of movie frames in case primary storage needs service.


- Network:
- To local network: 1x Dual 10GE SFP+ cards (2 ports)
- To the camera computer: 10 GB Fiber direct connection - SFP+ optical module for 10GBASE-LR
- To gpfs RAID: inifiniband - ConnectX-3 VPI adapter card, dual-port QSFP, FDR IB (56Gb/s) / 40GigE, PCIe 3.0 x8 8GT/s

- CPU: 2U Dual 2.1GHz Intel E5-2620 v4

- Memory: 128GB memory (8x 16GB)

- Storage: 9x 8TB 7.2K SATA drives, 1x 120GB SSD drive
- GPU: 2x NVIDIA PNY GeForce GTX 1080.


The software and configuration requirement is described here:

## Software requirement for preprocessing

### Processing:

The same basic requirement for appion processing server.
ctfFind4, motioncor2, gctf

### Activate the use of buffer server in leginon database.

1. Create a directory for all the data to be saved. For example /bufferdata/frames. Make it readable by the users.

2. Run myami/dbschema/tools/buffer_host_setup.py in Leginon environment. to link the buffer host and directory with the camera. This association signals Appion to find movie frames on the buffer server rather than the primary storage.

Two files are essential which we run as root all the time.

-   rawtransfer.py (Found in myami/leginon of your git clone) is used to move the movies from camera computer to the buffer server and change its name to match those of the Leginon sum images
-   transfermonitor.sh (Found in myami/leginon) is used to move the movies to the primary storage.


-   A third program run as cron job that removes frame movies accumulate on the primary storage after they are expired (not included).

## What to do when primary storage is down

We stop transfermonitor.sh so that it does not try to copy the frames from the buffer server.

leginon.cfg on the leginon processing server can also be changed to point the summed images to store on the buffer server. In that case, leginondb.BufferHostData should be set to be disabled during this period using phpMyAdmin. I will make a better gui for it later.

In our case, we do happen to have a backup storage server from an older system which also has a second copy of all softwares we use for data collection so we have been pointing the summed data there instead.
