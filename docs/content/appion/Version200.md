version:"Appion/Leginon 2.0.0" will be the initial deployment of Appion. Work toward this milestone will focus on ease of installation and user friendliness as well as robustness.
The Version number is 2.0 so that Appion and Leginon may continue with the same versioning.

1.  **Deployment**
    1.  ~~Evaluate existing code and development tools~~ (#31)
        1.  Add a few features to aid process
    2.  ~~Evaluate and adopt issue tracking software (Redmine)~~ (#32)
    3.  ~~Setup an IDE to increase developer productivity~~ (#33)
    4.  ~~Regression Test Appion~~ (#34)
        1.  ~~Setup test environment~~
        2.  ~~Define testing process~~
        3.  ~~Setup test case tracking~~
    5.  ~~Migrate production code that is not under source control (ProjectDB)~~ (#7)
        1.  ~~Move the Login page to be the first thing user sees~~
        2.  ~~Use groups to give 3 permission levels~~
        3.  ~~Convert Project Sharing table to Sinedon format~~
        4.  ~~Move password code from Project_tools to DBEM~~
        5.  ~~Move Project_Tools directory under DBEM~~
        6.  ~~Create scripts to migrate data from old DB tables to new tables~~
        7.  ~~Try to fix our user database by hand, or just require users to re-register.~~
    6.  ~~Create a web interface for configuration~~ (#35)
        1.  ~~Combine config files~~
        2.  ~~Tweak include paths~~
    7.  ~~Reduce number of repositories required for install~~ (#36)
        1.  ~~Combine DBEM and Project_Tools so that web parts are in single dir~~ (#7)
        2.  ~~Move all appion and leginon code into single repository~~ (#36)
    8.  Distribute compatible versions of dependencies from a single location (#37)
    9.  Create tools for troubleshooting (#38)
        1.  Tool to check the versions of dependencies are correct
    10. Make sure the mrc module installation works well (#34)
    11. Improve documentation (#40)
        1.  Convert docbook to redmine
        2.  ~~Convert google wiki to redmine~~
        3.  *Change redmine URL*
    12. Standardize the web interface of appion (#41)
        1.  ~~Make the first page a login page, then display what user can see~~ (#7)

[`<Edit this page>](/appion/appionVersion200)
