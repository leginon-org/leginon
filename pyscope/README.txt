scope.py - a virtual class defining generic functions of a TEM
camera.py - a virtual class defining generic functions of a CCD camera
tecnai.py - implements scope.py for the Tecnai TEM
tietz.py - implements camera.py for the Tietz CCD camera
gatan.py - implemenets camera.py for the Gatan CCD camera
tecnaicom.py - generated python COM wrapper for Tecnai Scripting
ldcom.py - generated python COM wrapper for Low Dose Module
tietzcom.py - generated python COM wrapper for Tietz CAMC
gatancom.py - generated python COM wrapper for Gatan (tecnaiccd.dll)
*dict.py - dictionary wrappers for generic scope and camera modules,
           allows access in scope['magnification'] = 100 format
emserver.py - XML-RPC server wrapper for networked commands
client.py - a wrapper for creating a XML-RPC networked client that can access
            in 'dictionary' format
RPCServer.py - run an instance of Tecnai and Gatan servers

The basic architecture of emScope is a client/server application. The emScope
server is an interface to a device such as the Tecnai or a CCD camera that
allows function calls to be made over the network by the emScope client.

The emScope server is an XML-RPC server implementation inherehited from the
standard Python XML-RPC server implementation. It allows calls to be made to
an instance of a scope or camera class over the network.

The scope and camera classes are virtual classes that define a universal set
of TEM and CCD Camera functions, allowing transparent use of different TEM
and CCD Cameras with the same interface. This allows a software package using
emScope to be able to run with a different type of camera or scope without
any modification.

The key to this model working is providing a real implementation of the scope
and camera classes. There are currently one TEM and two camera implementations
supporting Tecnai TEM along with Gatan and Tietz CCD cameras.

The emScope client is a small class that allows the Python dictonary-like
calls to be made over the network. Programs using emScope with use only
this class.

In addition to making standard calls to an instance of scope or camera
(actually and instance of the inherited class such as tecnai, gatan or tietz)
the scope or camera can be conveniently accessed by a Python dictionary-like 
interface.

The server is run on the machine that the device and COM module is located on.
The client is run (imported for use by an application) on any machine
networked with the server machine.

client example, with server running on machine 'tecnai' at port 8000:

import client

# instantiate a client
emclient = client.client('http://tecnai:8000')

# get the mag using the traditional interface
mag = emclient.getMagnification()
# set the mag using the traditional interface
emclient.setMagnification(mag)

# get the mag using the dictionary interface
mag = emclient['magnification']
# set the mag using the dictionary interface
emclient['magnification'] = mag

# get the entire "scope state" using the dictionary interface
state = emclient.copy()

The emScope server internals basically go through the following steps:
1. Creates an instance of XML-RPC server emserver.
-> Instantiates an instance of scopedict or cameradict (wrapper for
dictionary implementation.
-> Instantiate an instance of tecnai, tietz, or gatan.
-> Loads the COM module wrapper in python
-> Implements functions defined by scope, camera or raises NotImplemented
   exception
2. Runs, waiting for incoming requests from client.

