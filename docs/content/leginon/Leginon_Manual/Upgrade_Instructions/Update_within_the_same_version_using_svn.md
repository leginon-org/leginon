From time to time, we discover critical bugs that users are encouraged to update within the branch (x.x version) that they have checked out. Here is how to update when these situation arrives.

## You still have the svn check out of the whole myami superpackage:

1.  Go to the myami directory
2.  Confirm that this checkout working sandbox is the branch you want:
    -   Linux
            svn info
3.  update the checkout
    -   Linux
            svn update
    -   Windows
            RIght-click on the checkout top folder icon to select TotoisSVN Update

        
        You should see what has been changed by the update
4.  For the each of the **python subpackage** that changes are made, redo the python installation with the same command you used originally. For example, if changes were made in leginon subpackage, you would install leginon by
    -   Linux
            cd /_your_myami_svn_checkout_/leginon
            python setup.py install
    -   Windows from command line
            cd _your_myami_svn_checkout_\leginon
            C:\Python25\python.exe setup.py install
5.  For changes made in myamiweb, you should just copy individual files involved to your webserver at the relevant locations. You may also replace the whole myamiweb directory over, but you will then need to cp config.php from the old copy into the new one.
