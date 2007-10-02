#include "main.h"


/*
**
** Tilt Angle Calculator
**
*/

PyObject* tiltang(PyObject *self, PyObject *args) {
	/* Convert python variables */
	PyObject *a1, *a2;

	PyObject *pynull = PyInt_FromLong(0);

	float arealim;
	if (!PyArg_ParseTuple(args, "OOf", &a1, &a2, &arealim))
		return pynull;

	float lenlim = sqrt(arealim);
	//lenlim = fround(lenlim, 4);
	//printf("Area limit: %.1f\tLength limit: %.1f\n", arealim, lenlim);

	/* Take the smallest dimension as maximum dimension */
	//printf("Dim: %d\n", PyArray_DIMS(a1)[0]);
	//printf("Dim: %d\n", PyArray_DIMS(a2)[0]);
	int npoint = MIN(PyArray_DIMS(a1)[0], PyArray_DIMS(a2)[0]);

	/* Requires 3 points for a measurement*/
	if (npoint < 3)
		return pynull;
	//long posstri = factorial(npoint) / factorial(npoint - 3) / 6;
	long posstri = npoint*(npoint-1)*(npoint-2) / 6;
	//printf("TOTAL triangles: %ld, npoint: %d\n", posstri, npoint);

	int i,j,k;
	long badarea=0, badlen=0;
	double numtri=0;
	double tottri=0, sum=0, sumsq=0;
	double wtot=0, wsum=0, wsqtot=0, wsumsq=0;
	for (i = 0; i < npoint-2; i++) {
		for (j = i+1; j < npoint-1; j++) {
			for (k = j+1; k < npoint; k++) {
				/* Calc area in first image: */
				//printf("i,j,k: %d,%d,%d\n", i+1,j+1,k+1);

				int x1i = *((int *)PyArray_GETPTR2(a1,i,0));
				int x1j = *((int *)PyArray_GETPTR2(a1,j,0));
				int x1k = *((int *)PyArray_GETPTR2(a1,k,0));
				int y1i = *((int *)PyArray_GETPTR2(a1,i,1));
				int y1j = *((int *)PyArray_GETPTR2(a1,j,1));
				int y1k = *((int *)PyArray_GETPTR2(a1,k,1));

				int x1a	= x1j - x1i;
				int y1a	= y1j - y1i;
				int x1b	= x1k - x1i;
				int y1b	= y1k - y1i;
				//printf("%d * %d - %d * %d\n", xu1,yu2,xu2,yu1);

				double area1 = fabs(x1a * y1b - x1b * y1a);
				int len1a = fabs(x1a) + fabs(y1a);
				int len1b = fabs(x1b) + fabs(y1b);
				//printf("\nImage 1 Area:  %.0f\t", area1);
				tottri++;

				/* Check if area too small, break if it is */
				if (area1 < arealim) {
					badarea++;
					continue;
				} else if (len1a < lenlim || len1b < lenlim) {
					badlen++;
					continue;
				}

				/* Calc area in second image: */
				int x2i = *((int *)PyArray_GETPTR2(a2,i,0));
				int x2j = *((int *)PyArray_GETPTR2(a2,j,0));
				int x2k = *((int *)PyArray_GETPTR2(a2,k,0));
				int y2i = *((int *)PyArray_GETPTR2(a2,i,1));
				int y2j = *((int *)PyArray_GETPTR2(a2,j,1));
				int y2k = *((int *)PyArray_GETPTR2(a2,k,1));
				//printf("%d %d\n", x2i, y2i);

				int x2a	= x2j - x2i;
				int y2a	= y2j - y2i;
				int x2b	= x2k - x2i;
				int y2b	= y2k - y2i;

				double area2 = fabs(x2a * y2b - x2b * y2a);
				int len2a = fabs(x2a) + fabs(y2a);
				int len2b = fabs(x2b) + fabs(y2b);
				//printf("Image 2 Area:  %.0f", area2);

				/* Check if area too small, break if it is */
				if (area2 < arealim) {
					badarea++;
					continue;
				} else if (len2a < lenlim || len2b < lenlim) {
					badlen++;
					continue;
				}

				// Neil: Below Not general enough
				/* Area in tilted image should be <= area in untilted */
				double ratio = area2 / area1;
				double theta;
				if (ratio <= 1.0) {
					theta = acos(ratio);
				} else {
					//printf("\nERROR: Check keys: (%d,%d,%d) for a bad point\n", i+1, j+1, k+1); 
					ratio = area1 / area2;
					theta = -1.0*acos(ratio);
				}
				//printf("theta:  %.3f\n", theta*RAD2DEG);
				double wfact = (area1 + area2) / (arealim + 5000.0);
				double weight = wfact*wfact;
				numtri += 1;
				sum +=    theta;
				sumsq +=  theta*theta;
				wtot +=   weight;
				wsqtot += weight*weight;
				wsum +=   theta*weight;
				wsumsq += theta*theta*weight;

				//printf("a1: %d, a2: %d, ratio: %.5f, theta: %.2f\n", (int) area1, (int) area2, ratio, theta*RAD2DEG);
			}
		}
	}
	//This causes seg fault
	//Py_DECREF(x1);
	//Py_DECREF(y1);
	//Py_DECREF(x2);
	//Py_DECREF(y2);
	if( posstri != tottri)
		printf("Areas used for theta: %.0f out of %.0f (%ld)\n", numtri, tottri, posstri); 

	if (numtri == 0) {
		printf("\nERROR: Unable to compute tilt angle; Need 3 triangles with area > arealim!\n");
		return pynull;
	}

	//printf("sum = %.3f sumsq = %.3f numtri = %.1f\n",sum,sumsq,numtri);
	double theta = sum / numtri;
	double wtheta = wsum / wtot;
	double top = numtri*sumsq - sum*sum;
	double thetadev;
	if( top < 0.001 ) {
		thetadev = 0;
	} else
		thetadev = sqrt( top / (numtri * (numtri - 1.0)) );
	//printf("%.3f = sqrt %.3f = %.3f / %.3f\n",thetadev,top/(numtri * (numtri - 1.0)),top,(numtri * (numtri - 1.0)));

	/* Weighted stdev, from http://pygsl.sourceforge.net/reference/pygsl/node36.html */
	double wtop = wsumsq*wtot - wsum*wsum;
	double wbot = wtot*wtot - wsqtot; // 1/(N-1) term
	//double wbot = wtot*wtot; // 1/N term
	double wthetadev = sqrt(wtop/wbot);
	//printf("tottri=%.1f, sum=%.1f, sumsq=%.1f, wtot=%.1f, wsum=%.1f, wsqtot=%.1f, wsumsq=%.1f\n",
	//	tottri, sum, sumsq, wtot, wsum, wsqtot, wsumsq);
	//printf("%.3f = sqrt %.3f = %.3f / %.3f\n",wthetadev,wtop/wbot,wtop,wbot);

	theta = theta * RAD2DEG;
	wtheta = wtheta * RAD2DEG;
	thetadev = thetadev * RAD2DEG;
	wthetadev = wthetadev * RAD2DEG;

	/* Convert results into python dictionary */

	PyObject *result = PyDict_New();

	PyObject *pytheta = PyFloat_FromDouble((double) theta);
	PyDict_SetItemString(result, "theta", pytheta);
	Py_DECREF(pytheta);

	PyObject *pywtheta = PyFloat_FromDouble((double) wtheta);
	PyDict_SetItemString(result, "wtheta", pywtheta);
	Py_DECREF(pywtheta);

	PyObject *pywthetadev = PyFloat_FromDouble((double) wthetadev);
	PyDict_SetItemString(result, "wthetadev", pywthetadev);
	Py_DECREF(pywthetadev);

	PyObject *pythetadev = PyFloat_FromDouble((double) thetadev);
	PyDict_SetItemString(result, "thetadev", pythetadev);
	Py_DECREF(pythetadev);

	PyObject *pytottri = PyInt_FromLong((long) tottri);
	PyDict_SetItemString(result, "tottri", pytottri);
	Py_DECREF(pytottri);

	PyObject *pyposstri = PyInt_FromLong((long) posstri);
	PyDict_SetItemString(result, "posstri", pyposstri);
	Py_DECREF(pyposstri);

	PyObject *pynumtri = PyInt_FromLong((long) numtri);
	PyDict_SetItemString(result, "numtri", pynumtri);
	Py_DECREF(pynumtri);

	PyObject *pybadarea = PyInt_FromLong((long) badarea);
	PyDict_SetItemString(result, "badarea", pybadarea);
	Py_DECREF(pybadarea);

	PyObject *pybadlen = PyInt_FromLong((long) badlen);
	PyDict_SetItemString(result, "badlen", pybadlen);
	Py_DECREF(pybadlen);

	PyObject *pyarealim = PyFloat_FromDouble((double) arealim);
	PyDict_SetItemString(result, "arealim", pyarealim);
	Py_DECREF(pyarealim);

	PyObject *pylenlim = PyFloat_FromDouble((double) lenlim);
	PyDict_SetItemString(result, "lenlim", pylenlim);
	Py_DECREF(pylenlim);

	Py_DECREF(pynull);

	return result;
}




