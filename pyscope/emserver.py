import SimpleXMLRPCServer
#import cameradict
#import gatandict

#virtual = cameradict.cameradict
#implement = gatandict.gatandict

def makeserver(emdict, host, port):
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
    return server
