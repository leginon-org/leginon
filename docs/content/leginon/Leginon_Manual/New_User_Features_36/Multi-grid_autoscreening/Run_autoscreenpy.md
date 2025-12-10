If you have installed leginon, autoscreen.py is copied to script directory like start-leginon.py. Otherwise, you will find it under leginon directory.

    autoscreen.py

It will ask a few questions

    Enter autoloader cassette-grid mapping filename (leave it blank to use gui): /Users/acheng/grid.list
    Full workflow or atlas only (full/atlas): full
    Enter an old session name to base new sessions on: 22mar02a
    Enter Z stage height to return to in um (default: the old sessionvalue 0.0): 

The rest is automated.

## Things it will do for each grid:

1.  create and switch to a different session
2.  copy presets from the example session
3.  start idle and error slack notification
4.  unload last grid and load the current grid
5.  acquire atlas
6.  submit targets found on the atlas if full workflow is to be performed.
7.  go through MSI flow as specified in the example session.

If you need to modify the settings, you can still do so through leginon gui. It will be used next time the node is engaged.
