import SimpleXMLRPCServer
#import cameradict
#import gatandict

#virtual = cameradict.cameradict
#implement = gatandict.gatandict

def makeserver(virtual, implement, host, port):
    class emdict(implement, virtual):
        def __init__(self):
            if(dir(virtual).count('__init__')):
                virtual.__init__(self)
            if(dir(implement).count('__init__')):
                implement.__init__(self)
        def __del__(self):
            if(dir(virtual).count('__del__')):
                virtual.__del__(self)
            if(dir(implement).count('__del__')):
                implement.__del__(self)

    class emserver(emdict):
        def _dispatch(self, method, params):
            try:
                func = getattr(self, method.replace("export", ""))
            except AttributeError:
                raise Exception('method "%s" is not supported' % method)
            else:
                return apply(func, params)

    server = SimpleXMLRPCServer.SimpleXMLRPCServer((host, port))
    server.register_instance(emserver())
#    server.serve_forever()
    return server
