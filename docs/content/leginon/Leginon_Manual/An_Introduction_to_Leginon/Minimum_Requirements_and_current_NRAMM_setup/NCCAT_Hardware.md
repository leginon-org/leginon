This is still being built and will support

1 x Hitatchi HT7800
1 x TFS Glacios with Ceta-D
3 x TFS Krios with Ceta, and Gatan K3
1 x TFS Krios with Falcon 4

All microscopes use Leginon for data collection and Appion for preprocessing (defined as frame alignment/ctf estimation/particle picking) and on the same database server and together has ? web servers to serve the images for users to view and/or as Appion gui to construct the preprocessing commands. What is listed does not include infrastructure for 2D/3D classification and other post-processing.

## Network

All hardware mentioned below as well as the instruments are on a local 10 GB copper network.

## Leginon control or processing work station

One station per scope. For example,

CPU 8 x Intel i7-6700 @ 3.40GHz
MemoryL 16 GB
Storage: 50G HDD

## Database server

Dell R730 with (2) Intel E5-2689 3.1GHz, lOCore CPUs,
Memory: 128GB of RAM,
Storage: (2) 120GB HDD, (1) 800GB SSD

## Web server

Internet accessible: for use from outside the building

-   CPU: 8 x Intel Xeon L5410 @ 2.33GHz
-   Memory: 8 GB + 8 GB swap

## Frame processing server (One per microscope)

### K2/Falcon 4

An ingestion or buffer server to process frames before it goes to gpfs primary storage. This is reserved to the person using the scope.


- Network:
- To local network: 1x Dual 10GE SFP+ cards (2 ports)
- To the camera computer: 10 GB Fiber direct connection - SFP+ optical module for 10GBASE-LR
- To gpfs RAID: inifiniband - ConnectX-3 VPI adapter card, dual-port QSFP, FDR IB (56Gb/s) / 40GigE, PCIe 3.0 x8 8GT/s

- CPU: 2U Dual 2.1GHz Intel E5-2620 v4

- Memory: 128GB memory (8x 16GB)

- Storage: 9x 8TB 7.2K SATA drives, 1x 120GB SSD drive
- GPU: 2x NVIDIA PNY GeForce GTX 1080.


## Primary Storage

BEGFS ? pB
