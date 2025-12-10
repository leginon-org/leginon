## Add student's T distribution to maxlike alignment

-   Problem statement: Add student's T distribution to maxlike alignment, see #552
-   Goal: allow user to use the `-student` option for maxlike alignment using a radio button
-   Publication: http://www.ncbi.nlm.nih.gov/pubmed/19564687
-   Steps to implement:
    *# add feature to python code
    *## add command line input
    *## check flag to add to xmipp program
    *## insert value into database
    *## confirm python works by running source:trunk/appion/check.sh
    *## svn up; svn commit with Bug/Feature #
    *# add feature to web page
    *## add radio button to web page
    *## add help message
    *## receive variable from $_POST
    *## check if value is valid
    *## add flag to command line
    *## check PHP works by running source:trunk/myamiweb/processing/check.sh
    *## svn up; svn commit with Bug/Feature #

## Add an output directory to hierarchical classification

-   You cannot change the directory if the filesystem is full.
    *# check how outdir is defined within the program
    *# add `<input type='text' >` box to define the out dir
