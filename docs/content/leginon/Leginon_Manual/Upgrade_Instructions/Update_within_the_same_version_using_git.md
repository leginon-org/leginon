From time to time, we discover critical bugs that users are encouraged to update within the branch (x.x version) that they have checked out. Here is how to update when these situation arrives.

## You still have the git clone of the whole myami superpackage (May still be in /tmp/myami if you used autoinstaller):

1.  Go to the myami directory
2.  Confirm that this checkout working sandbox is the branch you want:
    -   Linux
            git status
3.  update the clone
    -   Linux
            git pull
    -   Windows
            RIght-click on the myami top folder icon to select GitBash Here, and then type in there:
            git pull

        
        You should see what has been changed by the update
4.  For the each of the **python subpackage** that changes are made, redo the python installation with the same command you used originally. For example, if changes were made in leginon subpackage, you would install leginon by
    -   Linux
            cd /_your_myami_git_clone_/leginon
            python setup.py install
    -   Windows from command line
            cd _your_myami_git_clone_\leginon
            C:\Python25\python.exe setup.py install
5.  For changes made in myamiweb, you should just copy individual files involved to your webserver at the relevant locations. You may also replace the whole myamiweb directory over, but you will then need to cp config.php from the old copy into the new one.
