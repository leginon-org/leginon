#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import SimpleXMLRPCServer
import threading
import sys
sys.coinit_flags = 0
import pythoncom
import emserver
import scopedict
import cameradict
import tecnai
import gatan
import client
import socket
import Tkinter
import Pmw

class RPCServerGUI:
    def __del__(self):
        pythoncom.CoUninitialize()

    def __init__(self, parent):
        pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
        self.hostname = socket.gethostname()

        self.gui = {'scope' : {}, 'camera' : {}}
        guis = ['scope', 'camera']
        
        grouplabels = ["Scope RPC Server", "Camera RPC Server"]

        ports = [8000, 8001]
        handlers = [self.doscope, self.docamera]
        servers = [self.scopeserve, self.cameraserve]
        
        for i in range(len(guis)):
            self.gui[guis[i]]['group label'] = grouplabels[i]
            self.gui[guis[i]]['hostname'] = self.hostname
            self.gui[guis[i]]['port'] = ports[i]
            self.gui[guis[i]]['handler'] = handlers[i]
            self.gui[guis[i]]['server'] = servers[i]
            
        for key in guis:
            self.gui[key]['running'] = 0
            self.gui[key]['group'] = Pmw.Group(parent, tag_text = self.gui[key]['group label'])
            self.gui[key]['group'].pack(side = 'top', padx = 5, pady = 5)
            self.gui[key]['interior group'] = Pmw.Group(self.gui[key]['group'].interior())
            self.gui[key]['interior group'].component('ring').configure(borderwidth = 0)
            self.gui[key]['interior group'].pack(side = 'top', padx = 0, pady = 0)
            self.gui[key]['run light'] = Tkinter.Frame(self.gui[key]['interior group'].interior(),
                                                       height = 10,
                                                       width = 10,
                                                       bg = 'red',
                                                       borderwidth = 2,
                                                       relief = "sunken")
            self.gui[key]['run light'].pack(side = 'left', padx = 5, pady = 5)
            self.gui[key]['name entry'] = Pmw.EntryField(self.gui[key]['interior group'].interior(),
                                    value = self.gui[key]['hostname'],
                                    validate = None)
            self.gui[key]['name entry'].pack(side = 'left', padx = 5, pady = 5)
            self.gui[key]['port entry'] = Pmw.EntryField(self.gui[key]['interior group'].interior(),
                                    value = self.gui[key]['port'],
                                    validate = None)
            self.gui[key]['port entry'].component('entry').configure(width = 5)
            self.gui[key]['port entry'].pack(side = 'left', padx = 5, pady = 5)
            self.gui[key]['button'] = Tkinter.Button(self.gui[key]['interior group'].interior(),
                                                     text = "Start",
                                                     command = self.gui[key]['handler'])
            self.gui[key]['button'].pack(side = 'left', padx = 5, pady = 5)
        
    def serve(self, key):
        while self.gui[key]['running']:
#            self.gui[key]['rpc'].handle_request()
            try:
                request, client_address = self.gui[key]['rpc'].get_request()
            except socket.error:
                return

            self.gui[key]['run light'].configure(bg = 'yellow')

            if self.gui[key]['rpc'].verify_request(request, client_address):
                try:
                    self.gui[key]['rpc'].process_request(request, client_address)
                except:
                    self.gui[key]['rpc'].handle_error(request, client_address)
                    self.gui[key]['rpc'].close_request(request)

            self.gui[key]['run light'].configure(bg = 'green')

        del self.gui[key]['rpc']
        self.gui[key]['run light'].configure(bg = 'red')
        self.gui[key]['button'].configure(text = "Start")
#        print key + "serve quit"

    def scopeserve(self):
        self.serve('scope')
    def cameraserve(self):
        self.serve('camera')
        
    def do(self, key, virt, implement):
        if self.gui[key]['running']:
            # kill the thread
            self.gui[key]['running'] = 0
            clnt = client.client("http://" + self.gui[key]['name entry'].get() + ':' + self.gui[key]['port entry'].get())
            try:
                clnt.prod()
            except:
                pass
        else:
            self.gui[key]['running'] = 1
            self.gui[key]['run light'].configure(bg = 'green')
            self.gui[key]['button'].configure(text = "Stop")
            self.gui[key]['rpc'] = emserver.makeserver(virt,
                                                       implement,
                                                       self.gui[key]['name entry'].get(),
                                                       int(self.gui[key]['port entry'].get()))
            #self.gui[key]['thread'] = threading.Thread(None, self.gui[key]['rpc'].serve_forever, None, (), {})
            self.gui[key]['thread'] = threading.Thread(None, self.gui[key]['server'], None, (), {})
            self.gui[key]['thread'].start()

    def doscope(self):
#        print "calling doscope"
        self.do('scope', scopedict.scopedict, tecnai.tecnai)
    def docamera(self):
#        print "calling docamera"
        self.do('camera', cameradict.cameradict, gatan.gatan)

if __name__ == '__main__':
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title("RPC Servers")
    widget = RPCServerGUI(root)
    root.mainloop()
