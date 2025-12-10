imcache uses redux and replaces the old myamiweb caching system that used mrc2any. It queries the database leginondata and check the cache_path for uncached images and convert them to jpeg images. These jpeg images can be 94 x smaller than the mrc 4kx4k image. Therefore, using imcache will significantly increase the image load time from the image viewer. A default size power spectrum image is also cached.

## Installation

1.  Follow [Web Server Installation](/leginon/Leginon_Manual/Complete_Installation/Web_Server_Installation) with modification for redux.
2.  Install pyami, sinedon, redux on the webserver machine
3.  Configure sinedon.cfg for your database
4.  imcache can found in your myamiweb installation in the folder myamiweb/imcache/

## Configurations:

### configure imcache

    > cd /YourMyamiWeb/imcache
    > edit imcacheconfig.py

Modify the line

    cache_path = '/srv/cache/myamiweb'


to the path you want to use as the base path for the cache to be stored. The path must exist and writable by whoever starts imcached

### Assign the same cache path in myamiweb

-   At myamiweb/config.php
        define('ENABLE_CACHE', true);
        define('CACHE_PATH',"/srv/cache/myamiweb");

h2 Test Installation

1.  Start imcached in its installed location with the reverse order caching
        ./imcached r

    
    If you have acquired any Leginon images prior to this, imcached will start converting them into jpeg.
2.  View a cached image in the imageviewer while checking redux log. jpeg, not mrc image should be requested by the imageviwer.

## Start imcache during data collection

1.  Start imcached in its installed location with the forward order caching in the background
        sudo nohup ./imcached f > /var/log/imcached.f
2.  Wait for the first image to be cached before starting the reverse caching
        sudo nohup ./imcached r > /var/log/imcached.r
