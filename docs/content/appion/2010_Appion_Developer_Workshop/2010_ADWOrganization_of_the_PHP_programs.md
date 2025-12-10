-   Location:
    -   /myami/myamiweb/processing


-   Sub Folders:
    -   `inc` --- include directory, common libraries like `appionlib`
    -   `js` --- javascript directory, contains `help.js` the help pop-up window text
    -   `img` --- image director, contains images like program logos (e.g., EMAN, Appion, Spider) and check, cross, and ext icons for image assessor
    -   `css` --- style sheets, custom look and feel of website, usually not modified


-   The include (`inc`) folder
    -   `appionloop.inc` --- contains the common interface for all appionLoop programs (CTF estimators, Particle pickers, and Make Stack)
    -   ~~`euler.inc`~~ --- depricated on the fly Euler plot generation script, was way too slow moved to python
    -   `menuprocessing.php` --- a single, giant function that generates the menu on the left side of all appion pages
    -   `particledata.inc` --- collection of all database queries, e.g., getStackIds(), getParticlesFromImageId(), getPixelSizeFromImgId(), or getStackIdFromReconId()
    -   `processing.inc` --- functions that are common to all Appion pages, e.g., processing_header(), referenceBox(), submitAppionJob(), getProjectId()
    -   `summarytables.inc` --- provides summary tables that are common on many pages, e.g., stacksummarytable(), alignstacksummarytable(), and modelsummarytable()


-   Important base scripts:
    -   `checkAppionJob.php` --- follow the progress of the job (common to all scripts, except reconstructions, see `checkRefineJobs.php`)
    -   `index.php` --- provides the final report with methods section for any exemplar reconstructions
    -   `config.php` --- the customization file for the
    -   `viewstack.php` --- the famous stack viewer


-   Ideal flow for a job process:
    -   *select program* (e.g., `selectParticleAlignment.php`) --- a selection page for each program that provides a detailed description to help user decide which on to use
    -   *run Appion script* (e.g., `runDogPicker.php`) --- setup parameters and run the program
    -   `checkAppionJob.php` --- follow the progress of the job (common to all scripts, except reconstructions, see `checkRefineJobs.php`)
    -   *process summary* (e.g., `stackhierarchy.php`) --- show all runs of that process type, e.g., stacks
    -   *process report* (e.g., `stackreport.php` --- report on a particular run of that process type, e.g. stack id 12
