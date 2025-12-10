## Perform system check

In addition to the downloads from our repository, there are several other requirements that you will get either from your OS installation source, or from its respective website. The system check in the Leginon package checks your system to see if you already have these requirements.

    cd myami/leginon/ 
    python syscheck.py

If python is not installed, this, of course will not run. If you see any lines like "* Failed...", then you have something missing. Otherwise, everything should result in "OK".
