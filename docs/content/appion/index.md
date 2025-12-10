# Overview

Appion is a "pipeline" for processing and analysis of EM images. Appion is integrated with [Leginon](/leginon/) data acquisition but can also be used stand-alone after uploading images (either digital or scanned micrographs) or particle stacks using a set of provided tools. Appion consists of a web based user interface linked to a set of python scripts that control several underlying integrated processing packages. All data input and output within Appion is managed using tightly integrated SQL databases. The goal is to have all control of the processing pipeline managed from a web based user interface and all output from the processing presented using web based viewing tools.

The underlying packages integrated into Appion include [MotionCor2](http://msg.ucsf.edu/em/software/motioncor2.html), [Gctf](http://www.mrc-lmb.cam.ac.uk/kzhang/), [EMAN](http://blake.bcm.edu/eman), [Spider](http://www.wadsworth.org/spider_doc/spider/docs/spider.html), [Frealign](http://emlab.rose2.brandeis.edu/), [Imagic](http://imagescience.de/imagic/), [XMIPP](http://xmipp.cnb.csic.es/), [IMOD](http://bio3d.colorado.edu/imod/), [ProTomo](http://www.electrontomography.org/), [ACE](http://emg.nysbc.org/redmine/projects/ami/wiki/ACE), [CTFFind and CTFTilt](http://emlab.rose2.brandeis.edu/), [findEM](http://nramm.scripps.edu/software/findem/), [DogPicker](http://nramm.scripps.edu/software/dogpicker/), [TiltPicker](http://emg.nysbc.org/redmine/projects/tiltpicker/wiki), [RMeasure](http://emlab.rose2.brandeis.edu/), [EM-BFACTOR](http://www.ual.es/~jjfdez/SW/embfactor.html), and [Chimera](http://www.cgl.ucsf.edu/chimera). These packages must be acknowledged by appropriate citations when used within Appion. Appropriate citations are provided on the individual pages in Appion as well as [here](/appion/Appion_citations).

## Current Release: [3.6](/appion/Appion_Manual/Version_Change_Log)

## Download Appion

Follow the Appion [installation instructions](/appion/Appion_Manual/Complete_Installation) to download and install Appion.

If you download Appion we strongly encourage you [register as an Appion user](http://emg.nysbc.org/redmine/account/register).
This will allow us to keep you informed of new releases, bug fixes, and other useful information, and also allow us to keep track of the user base which is important to ensure future support of the software.

## Appion User Manual

The **[Appion Manual](/appion/Appion_Manual)** includes:

-   a [description of Appion](/appion/Appion_Manual/An_Introduction_to_Appion),
-   [version change logs](/appion/Appion_Manual/Version_Change_Log),
-   [upgrade instructions](/appion/Appion_Manual/Upgrade_Instructions),
-   [installation instructions](/appion/Appion_Manual/Complete_Installation) and
-   [daily usage instructions](/appion/Appion_Manual/Appion_User_Guide)

## Appion Developer's Guide

The [developers guide](/appion/Developers_guide) is the primary resource for getting started with code development.
Appion is an open source project. You are free to contribute to it.

## Publications

### Primary Publications:

-   Lander, G.C.; Stagg, S.M., Voss, N.R., Cheng, A., Fellmann, D., Pulokas, J., Yoshioka, C., Irving, C., Mulder, A., Lau, P.W., *et al.* (2009). "Appion: an integrated, database-driven pipeline to facilitate EM image processing.". Journal of Structural Biology 166: 95-102. [PMID 19263523](http://www.ncbi.nlm.nih.gov/pubmed/19263523).


-   Voss, N.R.; Lyumkis D, Cheng A, Lau PW, Mulder A, Lander GC, *et al.* (2010). "A toolbox for ab initio 3-D reconstructions in single-particle electron microscopy.". Journal of Structural Biology 169 (3): 389-98. [PMID 20018246](http://www.ncbi.nlm.nih.gov/pubmed/20018246).


-   Stagg, S.M.; Lander GC, Quispe J, Voss NR, Cheng A, Bradlow H, Bradlow S, Carragher B, Potter CS (2008). "A test-bed for optimizing high-resolution single particle reconstructions". Journal of Structural Biology 163 (1): 29-39. [PMID 18534866](http://www.ncbi.nlm.nih.gov/pubmed/18534866).

### Other Citations:

-   Appropriate citations for integrated packages are provided on the individual pages in Appion as well as [here](/appion/Appion_citations).

## Software Availability and Licensing Information

Appion is released under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)

## Youtube videos

-   [An Introduction to Appion](http://www.youtube.com/watch?v=Wlxt_4yJKgA)
-   [TiltPicker Demonstration](http://www.youtube.com/watch?v=z7BqGJczmjU)

## Citations

View the entire collection of [Appion citations](/appion/Appion_citations).
