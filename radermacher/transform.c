#include "main.h"


/*
**
** Convert picks from coordinate system 1 to system 2
**
*/

PyObject* transform(PyObject *self, PyObject *args) {
	PyObject *a1, *a2;
	PyObject *pynull = PyInt_FromLong(0);
	double phi0, gamma0, theta0;
	if (!PyArg_ParseTuple(args, "OOfff", &a1, &a2, &theta0, &gamma0, &phi0))
		return pynull;

	int n = MIN(PyArray_DIMS(a1)[0], PyArray_DIMS(a2)[0]);
	if (n < 3) return pynull;

	/* Initialize variables */
	double rthe = theta0 * DEG2RAD;
	double rphi = phi0   * DEG2RAD;
	double rgam = gamma0 * DEG2RAD;

	/* Pre-calc cosines and sines */
	double cthe = cos(rthe);
	double cphi = cos(rphi);
	double cgam = cos(rgam);
	double sphi = sin(rphi);
	double sgam = sin(rgam);

	/* get the initial points for shifting */
	double a1x0 = (double) *((int *)PyArray_GETPTR2(a1,0,0));
	double a1y0 = (double) *((int *)PyArray_GETPTR2(a1,0,1));
	double a2x0 = (double) *((int *)PyArray_GETPTR2(a2,0,0));
	double a2y0 = (double) *((int *)PyArray_GETPTR2(a2,0,1));

	double *data = NULL;
	data = malloc(sizeof(double)*n*2);
	if ( data == NULL ) return pynull;
	double *xfinal = data;
	double *yfinal = data + n;

	int i;
	for (i = 0; i < n; i++) {
		double x1i = (double) *((int *)PyArray_GETPTR2(a1,i,0));
		double y1i = (double) *((int *)PyArray_GETPTR2(a1,i,1));
		//double x2i = (double) *((int *)PyArray_GETPTR2(a2,i,0));
		//double y2i = (double) *((int *)PyArray_GETPTR2(a2,i,1));
		xfinal[i] = ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * cphi
		          + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * sphi + a2x0;

		yfinal[i] = -((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * sphi
		           + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * cphi + a2y0;

	}

	npy_intp dimensions[2];
	dimensions[0] = 2;
	dimensions[1] = n;
	
	return PyArray_SimpleNewFromData( 2, dimensions, NPY_DOUBLE, xfinal );

}

