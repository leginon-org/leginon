#include <em.h>

PyObject *newinstance(char *modulename, char *classname, PyObject *pArgs) {

  PyObject *pModule, *pClass, *pInstance;

  pModule = PyImport_ImportModule(modulename);
  if(pModule == NULL) {
    fprintf(stderr, "Failed to import module: %s\n", modulename);
    PyErr_Print();
    return NULL;
  }

  pClass = PyObject_GetAttrString(pModule, classname);
  Py_DECREF(pModule);
  if(pClass == NULL) {
    fprintf(stderr, "Failed to locate class %s in module %s\n", 
                    classname, modulename);
    PyErr_Print();
    return NULL;
  }

  pInstance = PyEval_CallObject(pClass, pArgs);
  Py_DECREF(pClass);
  if(pInstance == NULL) {
    fprintf(stderr, "Failed to instantiate class\n");
    PyErr_Print();
    return NULL;
  }

  return pInstance;
}

PyObject *callmethod(PyObject *pInstance, char *methodname, PyObject *pArgs) {

  PyObject *pMethod, *pResult;

  pMethod = PyObject_GetAttrString(pInstance, methodname);
  if(pMethod == NULL) {
    fprintf(stderr, "Failed to locate method: %s\n", methodname);
    PyErr_Print();
    return NULL;
  }

  pResult = PyEval_CallObject(pMethod, pArgs);
  Py_DECREF(pMethod);
  if(pResult == NULL) {
    fprintf(stderr, "Call to method %s failed\n", methodname);
    PyErr_Print();
    return NULL;
  }

  return pResult;
}

PyObject *newclient(char *uri) {

  PyObject *pArgs, *pClient;

  pArgs = Py_BuildValue("(s)", uri);
  if(pArgs == NULL) {
    fprintf(stderr, "Failed to build value\n");
    return NULL;
  }

  pClient = newinstance("client", "client", pArgs);

  Py_DECREF(pArgs);

  return pClient;
}

void delclient(PyObject *pClient) {

  Py_DECREF(pClient);
  return;
}

PyObject *getitemfromstr(PyObject *pClient, char *str) {

  PyObject *pArgs, *pResult;

  pArgs = Py_BuildValue("(s)", str);
  if(pArgs == NULL) {
    fprintf(stderr, "Failed to build value\n");
    return NULL;
  }

  pResult = callmethod(pClient, "__getitem__", pArgs);
  Py_DECREF(pArgs);

  return pResult;
}

PyObject *addrgetitemfromstr(char *uri, char *str) {

  PyObject *pClient, *pResult;

  pClient = newclient(uri);
  if(pClient == NULL) {
    fprintf(stderr, "Failed to create client\n");
    return NULL;
  }

  pResult = getitemfromstr(pClient, str);
  delclient(pClient);

  return pResult;
}

int pobj2double(double *outval, PyObject *pResult) {

  if(pResult == NULL) {
    fprintf(stderr, "Result value is NULL\n");
    return -1;
  }

  PyArg_Parse(pResult, "d", outval);
  Py_DECREF(pResult);
  return 1;
}

int pobj2int(int *outval, PyObject *pResult) {

  if(pResult == NULL) {
    fprintf(stderr, "Result value is NULL\n");
    return -1;
  }

  PyArg_Parse(pResult, "i", outval);
  Py_DECREF(pResult);
  return 1;
}

int pobj2vector(double *outx, double *outy, PyObject *pResult) {

  if(pResult == NULL) {
    fprintf(stderr, "Result value is NULL\n");
    return -1;
  }

  PyArg_Parse(PyDict_GetItemString(pResult, "x"), "d", outx);
  PyArg_Parse(PyDict_GetItemString(pResult, "y"), "d", outy);

  Py_DECREF(pResult);

  return 1;
}

int pobj2stagevec(double *outx, double *outy, double *outz,
                                double *outa, PyObject *pResult) {

  if(pResult == NULL) {
    fprintf(stderr, "Result value is NULL\n");
    return -1;
  }

  PyArg_Parse(PyDict_GetItemString(pResult, "x"), "d", outx);
  PyArg_Parse(PyDict_GetItemString(pResult, "y"), "d", outy);
  PyArg_Parse(PyDict_GetItemString(pResult, "z"), "d", outz);
  PyArg_Parse(PyDict_GetItemString(pResult, "a"), "d", outa);

  Py_DECREF(pResult);

  return 1;
}

int pobj2str(char **outval, PyObject *pResult) {

  if(pResult == NULL) {
    fprintf(stderr, "Result value is NULL\n");
    return -1;
  }

  PyArg_Parse(pResult, "s", outval);
  Py_DECREF(pResult);
  return 1;
}

int b64str2ushorts(unsigned short **outval, int *size, PyObject *pResult) {

  PyObject *pBinString, *pArgs, *pArray, *pBuffer;

  pArgs = PyTuple_New(1);
  if(pArgs == NULL) {
    Py_DECREF(pResult);
    fprintf(stderr, "Failed create args tuple\n");
    return -1;
  }
  PyTuple_SetItem(pArgs, 0, pResult);

  pBinString = newinstance("base64", "decodestring", pArgs);
  Py_DECREF(pArgs);
//  Py_DECREF(pResult);
  if(pBinString == NULL) {
    fprintf(stderr, "Failed to convert base64 string\n");
    PyErr_Print();
    return -1;
  }

  pArgs = PyTuple_New(2);
  if(pArgs == NULL) {
    Py_DECREF(pBinString);
    fprintf(stderr, "Failed create args tuple\n");
    return -1;
  }
  PyTuple_SetItem(pArgs, 0, Py_BuildValue("s", "H"));
  PyTuple_SetItem(pArgs, 1, pBinString);

  pArray = newinstance("array", "array", pArgs);
  Py_DECREF(pArgs);
//  Py_DECREF(pResult);
  if(pArray == NULL) {
    fprintf(stderr, "Failed to convert base64 string\n");
    PyErr_Print();
    return -1;
  }

  pBuffer = PyBuffer_FromObject(pArray, 0, Py_END_OF_BUFFER);
  Py_DECREF(pArray);
  if(pBuffer == NULL) {
    fprintf(stderr, "Failed to create buffer from array\n");
    PyErr_Print();
    return -1;
  }

  if(PyObject_AsReadBuffer(pBuffer, (const void **)outval, size) != 0) {
    fprintf(stderr, "Failed to create ushort buffer from array\n");
    PyErr_Print();
    return -1;
  }
  return 1;
}

PyObject *setitemfromstr(PyObject *pClient, char *str, PyObject *pVal) {

  PyObject *pString, *pArgs, *pResult;

  pString = Py_BuildValue("s", str);
  if(pString == NULL) {
    fprintf(stderr, "Failed to build value\n");
    return NULL;
  }
  pArgs = PyTuple_New(2);
  if(pArgs == NULL) {
    Py_DECREF(pString);
    fprintf(stderr, "Failed create args tuple\n");
    return NULL;
  }
  PyTuple_SetItem(pArgs, 0, pString);
  PyTuple_SetItem(pArgs, 1, pVal);

  pResult = callmethod(pClient, "__setitem__", pArgs);
//  Py_DECREF(pString);
//  Py_DECREF(pVal);
  Py_DECREF(pArgs);

  return pResult;
}

PyObject *addrsetitemfromstr(char *uri, char *str, PyObject *pVal) {

  PyObject *pClient, *pResult;

  pClient = newclient(uri);
  if(pClient == NULL) {
    fprintf(stderr, "Failed to create client\n");
    return NULL;
  }

  pResult = setitemfromstr(pClient, str, pVal);
  delclient(pClient);

  return pResult;
}

PyObject *double2pobj(double inval) {

  PyObject *pResult;

  pResult = Py_BuildValue("d", inval);
  if(pResult == NULL)
    fprintf(stderr, "Failed to build value\n");

  return pResult;
  // remember to Py_DECREF pResult
}

PyObject *int2pobj(int inval) {

  PyObject *pResult;

  pResult = Py_BuildValue("i", inval);
  if(pResult == NULL)
    fprintf(stderr, "Failed to build value\n");

  return pResult;
  // remember to Py_DECREF pResult
}

PyObject *vector2pobj(double inx, double iny) {

  PyObject *pResult;

  pResult = Py_BuildValue("{s:d,s:d}", "x", inx, "y", iny);
  if(pResult == NULL)
    fprintf(stderr, "Failed to build value\n");

  return pResult;
  // remember to Py_DECREF pResult
}

PyObject *stagevec2pobj(double inx, double iny, double inz, double ina) {

  PyObject *pResult;

  pResult = Py_BuildValue("{s:d,s:d,s:d,s:d}", "x", inx, "y", iny,
                                               "z", inz, "a", ina);
  if(pResult == NULL)
    fprintf(stderr, "Failed to build value\n");

  return pResult;
  // remember to Py_DECREF pResult
}

PyObject *str2pobj(char *inval) {

  PyObject *pResult;

  pResult = Py_BuildValue("s", inval);
  if(pResult == NULL)
    fprintf(stderr, "Failed to build value\n");

  return pResult;
  // remember to Py_DECREF pResult
}

