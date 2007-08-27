#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>

#ifndef radermacher
  #define radermacher
  PyObject* tiltang(PyObject *self, PyObject *args);
  PyObject* willsq(PyObject *self, PyObject *args);
  int mircol(int n, int m, int mm, double a[4][5], double eps, double x[]);
#endif
