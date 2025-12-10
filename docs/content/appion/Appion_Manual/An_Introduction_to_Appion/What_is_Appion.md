Appion is a "pipeline" for single particle reconstruction. Appion is integrated with Leginon data acquisition but can also be used stand-alone after uploading images (either digital or scanned micrographs) or stackes using a set of provided tools. Appion consists of a web based user interface linked to a set of python scripts that control several underlying integrated processing packages. These include EMAN, Spider, Frealighn, Imagic, XMIPP, findEM, ACE, Chimera. All data input and output is managed using tightly integrated MySQL databases. The goal is to have all control of the processing pipeline managed from the web based user interface and all output from the processing presented using web based viewing tools.
These notes are provided as a rough guide to using the pipeline but are not guaranteed to be up to date or accurate.

Appion users usually start off at a web page that presents them with a range of options for processing, reconstruction, analysis. This may look something like the following:

![](images/Picture_6.png)

The user can select to proceed with any of the steps in the left hand menu options but some of these may be dependent on earlier steps. For example a stack cannot be made until particles have been selected. After any of the steps has been run the user can chose to view the results by clicking on the "completed" or "available" labels.

Appion and Leginon depend on the same basic architecture so you can install either one or both together with almost no extra effort. You will need to perform the same basic three parts of system installation for either or both packages. Following this basic installation, if you want to run Leginon on the microscope, you will need to perform a few additional steps, and instructions can be found in the [Leginon Manual](/appion/LeginonLeginon_Manual).

The four basic parts of Appion are :

-   **Processing server**- processing programs themselves or wrappers to processing packages generally in use by the 3DEM community.
-   **Database server** - where all data and processing is tracked.
-   **Web server** - php and java scripts that serve as the graphical user interface to the command scripts and results.
-   **File server** - where the images and processed results (e.g. stacks, volume data, etc) and all processing logs are stored.

Installation instructions for all of these parts are included in the Appion installation instructions.

In addition, Appion also needs:

-   **Processing packages** - which are installed on the processing server and are not currently distributed as part of Appion.

All 4 servers can run on the same machine. However, for an installation where high volume of data, processing and users is anticipated, it is recommended that the first three parts of the system are installed onto 3 separate computers.

[Credit >](/appion/Appion_Manual/An_Introduction_to_Appion/Authors)
