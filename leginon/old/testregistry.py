#!/usr/bin/env python
import time
import registry
import location

foo = registry.Registry()
bar = registry.RegistryEntry()
foo.addEntry(bar)
print foo.__str__()

bar1 = registry.NodeRegistryEntry([],[],location.Location('host', -1, -1))
foo.addEntry(bar1)
print foo.__str__()

bar2 = registry.DataRegistryEntry('my type',location.Location('host', -1, -1),time.localtime())
foo.addEntry(bar2)
print foo.__str__()

