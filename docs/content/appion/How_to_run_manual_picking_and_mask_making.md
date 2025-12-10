Manual picking and mask making use GUIs and require user interaction.
When running these at AMI, you can use amibox02 or amibox03.
When you ssh, you need to use the -X flag to tell the terminal to display the GUI.

    ssh -X amibox02

Then put the correct path to appion in front of the command, such as /ami/sw/bin/appion.

    /ami/sw/bin/appion makestack2.py --single=start.hed --selectionid=1002 --invert --normalized --maskassess=manualrun1 --boxsize=16 --description="test" --projectid=5 --preset=upload --session=10may13l35 --runname=stack7 --rundir=/ami/data00/appion/10may13l35/stacks/stack7 --no-rejects --no-wait --commit --reverse --limit=1 --continue
