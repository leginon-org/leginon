#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import emserver
import gatan
import scopedict
import socket
import tecnai
import threading
import tietz

if __name__ == '__main__':
    rpcscope = emserver.makeserver(scopedict.factory(tecnai.tecnai),
                              socket.gethostname(), 8000)
#    rpccamera = emserver.makeserver(methoddict.factory(tietz.Tietz),
    rpccamera = emserver.makeserver(methoddict.factory(gatan.Gatan),
                              socket.gethostname(), 8001)
    scopethread = threading.Thread(None, rpcscope.serve_forever, None, (), {})
    camerathread = threading.Thread(None, rpccamera.serve_forever, None, (), {})

    scopethread.start()
    camerathread.start()
