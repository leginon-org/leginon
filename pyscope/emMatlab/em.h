#include <Python.h>

PyObject *newinstance(char *modulename, char *classname, PyObject *pArgs);
PyObject *callmethod(PyObject *pInstance, char *methodname, PyObject *pArgs);

PyObject *newclient(char *uri);
void delclient(PyObject *pClient);

PyObject *getitemfromstr(PyObject *pClient, char *str);
PyObject *addrgetitemfromstr(char *uri, char *str);
int pobj2double(double *outval, PyObject *pResult);
int pobj2int(int *outval, PyObject *pResult);
int pobj2vector(double *outx, double *outy, PyObject *pResult);
int pobj2stagevec(double *outx, double *outy, double *outz,
                                double *outa, PyObject *pResult);
int pobj2str(char **outval, PyObject *pResult);
int b64str2ushorts(unsigned short **outval, int *size, PyObject *pResult);

PyObject *setitemfromstr(PyObject *pClient, char *str, PyObject *pVal);
PyObject *addrsetitemfromstr(char *uri, char *str, PyObject *pVal);
PyObject *double2pobj(double inval);
PyObject *int2pobj(int inval);
PyObject *vector2pobj(double inx, double iny);
PyObject *stagevec2pobj(double inx, double iny, double inz, double ina);
PyObject *str2pobj(char *inval);

