Feature #4686 was created to handle the case that the computer host default its IP mapping to a card not the one to connect to leginon need.

## [create the require ip mappings](/leginon/Add_host) in/etc/hosts (or on Winodows: C:\WINDOWS\system32\drivers\etc\hosts)

## Create specific host-ip pairing in pyami.cfg

1.  The template is myami/pyami/pyami.cfg.template in your myami git clone. Copy the template file to your global myami configuration directory. You should know where that is thru [this instruction](/leginon/Locate_global_config_directory_on_Windows)
2.  find out the name and ip addresses of the hosts that this computer needs to connect to.
3.  rename the copy as **pyami.cfg**
4.  edit pyami.cfg according to the mappings


    [my ip map]
    my-k3-computer: 192.168.0.1

    [other ip map]
    my-microscop-computer: 192.168.0.2
    my-leginon-computer: 192.168.0.3
    my-database-server: 192.168.0.4

## Testing

If you have done either python setup.py installation or PYTHONPATH mapping to the myami directories, you should be able to test.

### On Windows, double click your_myami_clone\pyami\mysocket.py

### On Linux, type in terminal

    cd your_myami_clone/pyami
    python mysocket.py

If the host ip mapping are correct, you should get [OK] in the tests.

    my-k3-computer ip mapping [OK]
    my-microscope-computer ip mapping [OK]
    my-leginon-computer ip mapping [OK]
    my-database-server ip mapping [OK]
