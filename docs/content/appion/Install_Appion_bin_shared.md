Since the appion package includes many executable scripts, it is important that you know where they are being installed. To prevent cluttering up the /usr/bin directory, you can specify an alternative path, typically /usr/local/bin, or a directory of your choice that you will later add to your PATH environment variable. Install appion like this:

    cd /path/to/myami-VERSION/appion
    sudo python setup.py install --install-scripts=/usr/local/bin/appion
