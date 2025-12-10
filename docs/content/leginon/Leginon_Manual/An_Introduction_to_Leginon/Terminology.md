## Application

A Leginon application is image acquisition process that is built of several smaller
pieces called 'nodes'. An application defines your preferred scheme for how to acquire
images. An application definition includes which nodes to use, how they are connected, and
where they are running (possibly distributed across several machines). These three concepts
of applications (nodes, events, launchers) are described in more detail below. A typical
application involves several stages of image acquisition and image processing. Once an
application is designed, it can be used repeatedly for different sessions. An application
design can be exported for use on other Leginon installations.

## Session

A session is defined as an execution from start to finish of a Leginon application. All
data (images, results, etc.) that are created by Leginon is associated with some session.
The first thing a user must do when starting Leginon is create a session, or continue an
existing session.

## Instrument

An instrument is the microscope/camera system used for acquiring data during a
particular session. The facility at which Leginon is installed may have several different
microscopes, each with a unique camera setup. Each system is an instance of an
Instrument.

## Node

Nodes are the building blocks of Leginon applications. Nodes are defined for specific
tasks. For instance, an "Acquisition" node is designed to acquire images when it receives
targets from another node, which is typically some type of 'TargetFinder' node. Nodes can
"publish" the data they create. This means they are making their data public for other nodes
to use. The other nodes can "research" to find a specific item of data. Nodes may
communicate with each other by generating "events".

## Event

An event is a message sent out from a node to notify other nodes that something of
interest has happened. A common example is to announce that some data has been published.
Another example is to announce that some process has finished. The declaration of which
events are routed between which nodes is part of the application design process.

## Manager

Manager is the master of all nodes in an application. Its existence is usually
transparent while running a session, but it is responsible for starting up the application
with all its nodes and event bindings. It works behind the scenes to ensure that events are
properly distributed throughout the system.

## Launcher

A Launcher is the parent process for a set of nodes. There is typically one launcher
running on each machine that you intend to have nodes running on. The assignment of which
nodes will be started on a particular launcher is defined as part of the application.

## Preset

A preset is a piece of data which encapsulates the state of an instrument. At any time,
the current state of an instrument (magnification, image shifts, camera settings, etc) can
be recorded for later use. There is a particular class of Node called the PresetsManager
which maintains a list of presets for the current Leginon session. These presets are used by
other nodes to set the state of the instrument prior to acquiring an image. This allows for
a series of images to be acquired at a consistent state, but possibly different targets (see
below). This is very similar to the "Low Dose" system on many microscopes, which consists of
a few presets like "Search", "Focus", and "Exposure". The Leginon PresetsManager is a more
generalized approach which allows for and unlimited number of presets to be used (like
several search presets at different magnifications, or multiple exposure presets at
different defocus).

## Target

A target is a location where an image will be acquired. Targets are often selected from
existing images (using a TargetFinder node). Acquisition nodes are responsible for
interpreting Targets and then acquiring images of them.

[< What is the Leginon System?](/leginon/Leginon_Manual/An_Introduction_to_Leginon/What_is_the_Leginon_System) | [Graphical User Interface >](/leginon/Leginon_Manual/An_Introduction_to_Leginon/Graphical_User_Interface)
