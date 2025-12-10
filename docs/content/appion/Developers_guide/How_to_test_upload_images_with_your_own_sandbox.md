Just had to do this so taking some notes:

## [the objective]{.underline}

I have images that I want to upload located in my home directory.
I want to use my sandbox on the web side of appion.
I want to use the wrapper/appion snapshot/beta appion for the python parts. However you want to call it, I just need a recent version.
I want to upload the images to my own private database that is located on the fly server.
When the images are uploaded, I want them stored in my home directory rather than on /ami/data00.

## [setup]{.underline}

### sinedon.cfg in home directory

Make sure sinedon.cfg is in your home directory and the host, user and password correspond to your database.
Make sure the projectdata and leginondata settings are set to the name of your db.

### leginon.cfg in home directory

Make sure leginon.cfg is in your home directory and the images path is set to a folder in your home directory.

### config.php located in your sandbox under myamiweb

Make sure the database information matches what is found in sinedon.cfg.

## [create the command]{.underline}

-   open myamiweb
    Go to fly/~your_username/myamiweb which has been set up per the instructions found under *Use Cronus3 or Fly to view your web app* in the [AMI Eclipse Quick Start Guide](/appion/Developers_guide/AMI_Eclipse_Quick_Start_Guide).


-   Go to or create a project for your images to be uploaded into.
-   make sure there is a database set for the project (ex. ap123)
-   click on [upload images to new session]
-   Under the *directory containing images* field copy the path to the images on your home directory ex. /home/your_username/dir1/dir2
-   Select *just show command*

## [execute the command]{.underline}

Fly does not have the python parts installed.
Guppy does not have access to your home directory to get the images.

1.  ssh into amibox02 or amibox03 to run uploadimage.py
2.  Copy and past the command that was provided by the web page into the terminal
3.  Add the path to the wrapper installation to make sure you are executing the most recent version of the python code.
    This is probably /opt/myamisnap/bin/appion and it should be pre-pended to the command.

example:

    /opt/myamisnap/bin/appion uploadImages.py --projectid=268 --image-dir=/home/amber/uploadedimages/pairedimages --mpix=1E-09 --type=defocalseries --images-per-series=2 --defocus-list=-1E-10,-2E-10 --mag=50000 --kv=120 --description="defocal test" --jobtype=uploadimage
