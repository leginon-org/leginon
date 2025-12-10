(Fly is a good choice since it is not a production server. You can create your own databases on Fly as well.)

1.  Open a terminal and go to your home directory: **$ cd ~**
2.  Create a directory called "ami_html" if it does not exist: **$ mkdir ami_html/**
3.  Change directories to ami_html: **$ cd ami_html**
4.  Create a symbolic link to the web app directory in your workspace: **$ ln -s /home/[username]/amiworkspace/myami/myamiweb**
5.  Try to browse to the project in a web browser ( http://cronus3/~username/myamiweb ). You should see an error because config.php failed to open. Keep reading "Create your config file" to fix this.
