### How to check out the code

To get the development trunk (where new features are added):

    svn co http://emg.nysbc.org/svn/myami/trunk myami/

To get a release version (Bug fixes only please):

    svn co http://emg.nysbc.org/svn/myami/branches/myami-2.2 myami-2.2/

To commit changes back use:

    svn commit --username [type-user-name-here]


The option ---username is needed when remote username differs from local.

### How to create a new branch in svn

[Information on branching.](http://svnbook.red-bean.com/en/1.1/ch04s02.html#svn-ch-4-sect-2.1)

1.  Before creating an official release branch, you need to update [myamiweb/xml/projectDefaultValues.xml](http://emg.nysbc.org/redmine/projects/appion/repository/entry/trunk/myamiweb/xml/projectDefaultValues.xml) which holds the version number.
    The version number is stored in the database at installation time.
     
2.  Create a new branch:
        $ svn copy http://emg.nysbc.org/svn/myami/trunk http://emg.nysbc.org/svn/myami/branches/myami-2.1 -m "Creating a branch for myami 2.1"

        Committed revision 14869.

    
     
3.  If this is a release branch, ask Sargis to make sure only a couple of people are allowed to check in changes to this branch.
