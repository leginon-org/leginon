Run the following script on any of the computer where you have done the update on.

On Linux:

    $PYTHONSITEPKG/leginon/cscheck.py

On Windows:

    C://Python25/Lib/site-packages/leginon/cscheck.py

You should get a list of microscope where you have saved images on in a Leginon session and the Cs values that you entered using schema-r15653.py. For example,

    TEM tecnai1234.Tecnai used in session 12jun07a has Cs value of 2.000e-03 m

Check that against the Cs value in instruments.cfg on the named microscope (tecnai1234 in this case) which is also listed in meters, like this:

    [tem]
    class: fei.Tecnai
    cs: 2.0e-3

**The two must match. Otherwise Leginon will complain and you may lose all your old calibrations.**

-   pre 3.3 Leginon version should see in instruments.cfg scope class as tecnai.Tecnai

[< How to Update from v2.1 (Microscope Windows Computer)](/leginon/Leginon_Manual/Upgrade_Instructions/Upgrade_to_Leginon_System_version_22_from_version_21/How_to_Update_from_v21_Microscope_Windows_Computer)
