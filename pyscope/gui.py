import Tkinter

class rpcgui:
    def __init__(self, master):
        self.master = master
        self.frame()
        self.button()
        self.entry("foo", 20)
        self.entry("123", 5)
        self.menu()
    def menu(self):
        self.m = Tkinter.Menu(self.f)
        self.m.add_command(label="localhost", command=self.start)
        self.m.add_command(label="amilab", command=self.start)
        #self.mb.insert(Tkinter.END, "localhost")
        #self.mb.insert(Tkinter.END, "amilab")
        #self.m.pack()
    def frame(self):
        self.f = Tkinter.Frame(self.master)
        self.f.pack()
    def button(self):
        self.b = Tkinter.Button(self.f, text="Start", command=self.start)
        self.b.pack()
    def entry(self, text, width):
        self.et = Tkinter.StringVar(self.f)
        self.et.set(text)
        self.e = Tkinter.Entry(self.f, {"textvariable":self.et,
                                             "width":width})
        self.e.pack()
    def start(self):
        print self.et.get()
        
if __name__ == '__main__':
    root = Tkinter.Tk()
    root.title("RPC Server")
    gui = rpcgui(root)
