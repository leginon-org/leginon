#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>

#ifndef M_PI
  #define M_PI 3.14159265358979323846
#endif

#ifndef DEG2RAD
  #define DEG2RAD 0.017453292519943
#endif

#ifndef RAD2DEG
  #define RAD2DEG 57.295779513082
#endif

#undef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))

#undef MAX
#define MAX(a,b) ((a) > (b) ? (a) : (b))

#ifndef radermacher
  #define radermacher
  PyObject* tiltang(PyObject *self, PyObject *args);
  PyObject* willsq(PyObject *self, PyObject *args);
  PyObject* transform(PyObject *self, PyObject *args);
  int mircol(int n, int m, int mm, double a[4][5], double eps, double x[]);
#endif
