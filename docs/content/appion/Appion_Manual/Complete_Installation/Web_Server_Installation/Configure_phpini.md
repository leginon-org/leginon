Edit the following items in php.ini (found as /etc/php.ini on CentOS and /etc/php5/apache2/php.ini on SuSE)

    sudo nano /etc/php.ini

so that they look like the following:

> error_reporting = E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED
>  
> display_errors = On
>  
> register_argc_argv = On
>  
> short_open_tag = On
>  
> max_execution_time = 300 ; Maximum execution time of each script, in seconds
> max_input_time = 300 ; Maximum amount of time each script may spend parsing request data
> memory_limit = 256M ; Maximum amount of memory a script may consume (8MB)

You may want to increase max_input_time and memory_limit if the server is heavily used. At NRAMM, max_input_time=600 and memory_limit=4000M.

You should also set timezone using one of the valid string found at http://www.php.net/manual/en/timezones.php like this:

> date.timezone = 'America/Los_Angeles'

[< Install Web Server Prerequisites](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_Web_Server_Prerequisites) | [Install Apache Web Server >](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_Apache_Web_Server)
