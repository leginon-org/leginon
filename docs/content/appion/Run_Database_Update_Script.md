## Run Database Update Script

Running the following script will indicate if you need to run any database update scripts.

    cd /your_download_area/myami/dbschema
    python schema_update.py

This will print out a list of commands to paste into a shell which will run database update scripts.
You can re-run schema_update.py at any time to update the list of which scripts still need to be run.
