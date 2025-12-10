## more info

http://cryoem.nysbc.org/CemRobotics.html

## instruments.cfg

    [TEM]
    class: jeol1230.jeol1230

## Testing pyscope instrument script functions

On the instrument host of the instrument, a TEM host that uses Tecnai class, for example, you can launch python command line window and try to create an instance of the instrument and then call a function such as getMagnifications in that like this:

    import pyscope.registry
    s = pyscope.registry.getClass('jeol1230')()
    s.getMagnifications()

## Potential problems

### import serial

    >>> import pyscope.registry
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\Python25\Lib\site-packages\pyscope\registry.py", line 9, in <module>
        import config
      File "c:\Python25\Lib\site-packages\pyscope\config.py", line 39, in <module>
        mod = imp.load_module(fullmodname, *args)
      File "c:\Python25\Lib\site-packages\pyscope\jeol1230.py", line 8, in <module>
        from pyscope import jeol1230lib
      File "c:\Python25\Lib\site-packages\pyscope\jeol1230lib.py", line 8, in <module>
        import serial
    ImportError: No module named serial
    >>>

you need to install "Python Serial Port Extensions" http://pypi.python.org/pypi/pyserial

### defocus.cfg

    >>> import pyscope.registry
    >>> s = pyscope.registry.getClass('jeol1230')()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\Python25\Lib\site-packages\pyscope\jeol1230.py", line 27, in __init__
        self.jeol1230lib = jeol1230lib.jeol1230lib()
      File "c:\Python25\Lib\site-packages\pyscope\jeol1230lib.py", line 25, in __init__
        self.zeroDefocus = self.readZeroDefocus()
      File "c:\Python25\Lib\site-packages\pyscope\jeol1230lib.py", line 35, in readZeroDefocus
        infile = open(self.defocusFile,"r")
    IOError: [Errno 2] No such file or directory: 'C:\Python25\Lib\site-packages\pyScope\defocus.cfg'
    >>>

create an empty file called defocus.cfg

### serial port permissions

    >>> import pyscope.registry
    >>> s = pyscope.registry.getClass('jeol1230')()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\python25\Lib\site-packages\pyscope\jeol1230.py", line 27, in __init__
        self.jeol1230lib = jeol1230lib.jeol1230lib()
      File "c:\python25\Lib\site-packages\pyscope\jeol1230lib.py", line 25, in __init__
        self.zeroDefocus = self.readZeroDefocus()
      File "c:\python25\Lib\site-packages\pyscope\jeol1230lib.py", line 37, in readZeroDefocus
        line = lines[0]
    IndexError: list index out of range
    >>> s = pyscope.registry.getClass('jeol1230')()
    close connection to JEOL1230 through COM1 port
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "c:\python25\Lib\site-packages\pyscope\jeol1230.py", line 27, in __init__
        self.jeol1230lib = jeol1230lib.jeol1230lib()
      File "c:\python25\Lib\site-packages\pyscope\jeol1230lib.py", line 18, in __init__
        self.ser = serial.Serial(port='COM1', baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff = 0, timeout=10, rt
    scts=0)
      File "serial\serialwin32.py", line 31, in __init__
        SerialBase.__init__(self, *args, **kwargs)
      File "serial\serialutil.py", line 261, in __init__
        self.open()
      File "serial\serialwin32.py", line 59, in open
        raise SerialException("could not open port %s: %s" % (self.portstr, ctypes.WinError()))
    serial.serialutil.SerialException: could not open port COM1: [Error 5] Access is denied.
    >>>
