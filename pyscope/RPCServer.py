import SimpleXMLRPCServer
import threading
import sys
sys.coinit_flags = 0
import pythoncom
import scopedict
import tecnai
import cameradict
import gatan
import emserver
import client

if __name__ == '__main__':
    pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
    rpcscope = emserver.makeserver(scopedict.scopedict, tecnai.tecnai,
                              'amilab8', 8000)
    #rpccamera = emserver.makeserver(cameradict.cameradict, gatan.gatan,
    #                          'amilab8', 8001)
    scopethread = threading.Thread(None, rpcscope.serve_forever, None, (), {})
    #camerathread = threading.Thread(None, rpccamera.serve_forever, None, (), {})

    scopethread.start()
    #camerathread.start()
