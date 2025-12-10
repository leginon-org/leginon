In this example, we want to find the dll for TEM Scripting and register it.

## Find the dll file for the type library.

1.  Navigate to C:\Python27\Lib\site-pacakges\pythoncom\client
2.  Open combrowse.py
3.  Expand Registered Type Libraries and find "TEM Scripting"
4.  Expand "Type Library" under TEM Scripting"
5.  You should find at the end of the list "Filname: 'C:\Tecnai\Scripting\StdScript.dll'
    ![](images/combrowse.png)

## Register the dll

With Windows comand line terminal

    cd C:\Tecnai\Scripting
    regsvr32 StdScript.dll
