NRAMM is located at Simons Electron Microscopy Center (SEMC) at New York Structural Biology Center.
We currently have 6 TEM.

1 x JEOL 1230 with Gatan UltraScan 4000
1 x FEI T-12 with TVIPS F416
1 x FEI F20 with DE-20 camera and TVIPS F416
3 x FEI Krios with Falcon |||, Ceta, and Gatan K2 Summit

All 6 microscopes use Leginon for data collection and Appion for preprocessing (defined as frame alignment/ctf estimation/particle picking) and on the same database server and together has 3 web servers to serve the images for users to view and/or as Appion gui to construct the preprocessing commands. What is listed does not include infrastructure for 2D/3D classification and other post-processing.

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

1. For local network only

-   CPU 4 x Intel Xeon @ 3.00GHz
-   Memory: 4 GB
-   Storage 700GB HDD

2. For local network only (This is one of the node on our processing cluster. Rather under used this way)

-   CPU 24 Intel Xeon E5-2670 v3 \@2.30GHz
-   Memory: 265 MB

3. Internet accessible: for guests and member institution to use from outside the building

-   CPU: 8 x Intel Xeon L5410 @ 2.33GHz
-   Memory: 8 GB + 8 GB swap

## Frame processing server (One per microscope)

### K2/Falcon |||

An ingestion or buffer server to process frames before it goes to gpfs primary storage. This is reserved to the person using the scope.


- Network:
- To local network: 1x Dual 10GE SFP+ cards (2 ports)
- To the camera computer: 10 GB Fiber direct connection - SFP+ optical module for 10GBASE-LR
- To gpfs RAID: inifiniband - ConnectX-3 VPI adapter card, dual-port QSFP, FDR IB (56Gb/s) / 40GigE, PCIe 3.0 x8 8GT/s

- CPU: 2U Dual 2.1GHz Intel E5-2620 v4

- Memory: 128GB memory (8x 16GB)

- Storage: 9x 8TB 7.2K SATA drives, 1x 120GB SSD drive
- GPU: 2x NVIDIA PNY GeForce GTX 1080.


### DE20

Direct Electron frame alignment program runs on CPUs. It has its dedicated computer.

-   CPU: 32 x Intel Xeon E5-2640 v2 @ 2.00 GHz
-   Memory: 132 GB RAM
-   Job scheduler Torque installed.

## Primary Storage

GPFS 1 pB

## [SEMC file storage policy](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Minimum_Requirements_and_current_NRAMM_setup/SEMC_file_storage_policy)
