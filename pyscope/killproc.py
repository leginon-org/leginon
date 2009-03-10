import time
import win32api, win32pdhutil, win32con
import win32pdh, string


# ***********************************************************************
# ***********************************************************************
def GetAllProcesses():
  object = "Process"
  items, instances = win32pdh.EnumObjectItems(None,None,object, 
win32pdh.PERF_DETAIL_WIZARD)
  return instances
# ***********************************************************************


# ***********************************************************************
# ***********************************************************************
def GetProcessID ( name ) :
  object = "Process"
  items, instances = win32pdh.EnumObjectItems(None,None,object, 
win32pdh.PERF_DETAIL_WIZARD)

  val = None
  if name in instances :
    hq = win32pdh.OpenQuery()
    hcs = []
    item = "ID Process"
    path = win32pdh.MakeCounterPath( (None,object,name, None, 0, item) )
    hcs.append(win32pdh.AddCounter(hq, path))
    win32pdh.CollectQueryData(hq)
    time.sleep(0.01)
    win32pdh.CollectQueryData(hq)

    for hc in hcs:
      type, val = win32pdh.GetFormattedCounterValue(hc, 
win32pdh.PDH_FMT_LONG)
      win32pdh.RemoveCounter(hc)
    win32pdh.CloseQuery(hq)
    return val
# ***********************************************************************


"""
THIS IS SLOW !!
def Kill_Process ( process ) :
  #get process id's for the given process name
  pids = win32pdhutil.FindPerformanceAttributesByName ( process )
  for p in pids:
    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, p) #get 
process handle
    win32api.TerminateProcess(handle,0) #kill by handle
    win32api.CloseHandle(handle)        #close api
"""

# ***********************************************************************
# ***********************************************************************
def Kill_Process_pid ( pid ) :
  handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid) #get process handle
  win32api.TerminateProcess(handle,0) #kill by handle
  win32api.CloseHandle(handle)        #close api
# ***********************************************************************


# ***********************************************************************
# ***********************************************************************
def Kill_Process ( name ) :
  pid = GetProcessID ( name)
  if pid:
    Kill_Process_pid ( pid )
# ***********************************************************************


# ***********************************************************************
# ***********************************************************************
if __name__ == "__main__":
  a = GetAllProcesses()
  print a

  process = 'UPD'
  Kill_Process ( process )
