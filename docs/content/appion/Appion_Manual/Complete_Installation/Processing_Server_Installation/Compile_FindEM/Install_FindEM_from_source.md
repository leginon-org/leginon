If the binary included with Appion does not work, or you wish to compile it yourself follow these instructions.

-   Download FindEM


-   Compile the libraries and binary


    $ make

-   Test findem.exe to see if it runs


    $ make test

**WARNING**
Only if the first part fails, you must add the path to libg2c.so library file.
Otherwise skip to next section.

-   locate libg2c.so library file


    $ ls /usr/lib/gcc/`uname -i`-redhat-linux/3.4.6/libg2c.so

    $ locate libg2c.so

-   Edit Makefile with location of libg2c.so


    EXLIBS=-L/usr/lib/gcc/i386-redhat-linux/3.4.6/ -lg2c

-   Re-compile

[Install FindEM ^](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Compile_FindEM)
