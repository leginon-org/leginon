import TecnaiCCDWrapper

foo = TecnaiCCDWrapper.acquire()
print foo
print foo.typecode(), foo.shape
