import SimpleXMLRPCServer
import threading
import sys
import socket
sys.coinit_flags = 0
import pythoncom
import scopedict
import tecnai
import cameradict
import tietz
import emserver
import client

if __name__ == '__main__':
    pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
    rpcscope = emserver.makeserver(scopedict.scopedict, tecnai.tecnai,
                              socket.gethostname(), 8000)
    rpccamera = emserver.makeserver(cameradict.cameradict, tietz.tietz,
                              socket.gethostname(), 8001)
    scopethread = threading.Thread(None, rpcscope.serve_forever, None, (), {})
    camerathread = threading.Thread(None, rpccamera.serve_forever, None, (), {})

    scopethread.start()
    #camerathread.start()
