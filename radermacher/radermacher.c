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

/*
float fround(float f, int n) {
	int i;
	float m = 1.0;
	for(i=0; i<=n; i++)
		m *= 10.0;
	int r = (int) (f*m);
	float result = ((float) r) / m;
	return result;
}
*/

long factorial(int n) {
	long fact=1;
	while(n > 0)
		fact *= n--;
	return fact;
}

/*
**
** Mircol ????
**
*/

int mircol(int n, int m, int mm, double a[4][5], double eps, double x[]) {
/*
** 4x4 Matrix Inversion
*/
	int i,ii,iii,j,jjj,k,kkk;
	int wurz[6];
	float epsq,s;

	epsq = eps * eps;

	for (i = 1; i <= n; i++) {
		wurz[i-1] = 1;
		s = a[i-1][i-1];
		if (i != 1) {
			iii = i -1;
			for (j = 1; j <= iii; j++) {
				if (!wurz[j-1])
					s = s + a[j-1][i-1] * a[j-1][i-1];
				else
					s = s - a[j-1][i-1] * a[j-1][i-1];
			}
		}
		if (s <= 0) {
			s = -s;
			wurz[i-1] = 0;
		}
		if (s < epsq)
			return -1;
	     
		a[i-1][i-1] = sqrt(s);
		iii         = i+1;

		for (k = iii; k <= mm; k++) { 
			s   = a[i-1][k-1];
			jjj = i-1;

			if (jjj >= 1) {
				for (j = 1; j <= jjj; j++) {
					if (!wurz[j-1])
						s = (s + a[j-1][i-1] * a[j-1][k-1]);
					else
						s = (s - a[j-1][i-1] * a[j-1][k-1]);
				}
			}

			if (!wurz[i-1])
				s = -s;

			a[i-1][k-1] = s / a[i-1][i-1];
		} 
	}

	for (k = 1; k <= m; k++) { 
		for ( ii = 1; ii <= n; ii++) {
			i   = n - ii + 1;
			s   = a[i-1][n+k-1];
			kkk = i+1;
			if ( kkk <= n) {
				for (j = kkk; j <= n; j++)
					s = s - x[j-1] * a[i-1][j-1];   
			}
			x[i-1] = s / a[i-1][i-1];
		} 
	}
	return 0;
}

/*
int diffFit(PyObject* a1, PyObject* a2, double theta, double gamma, double phi) {
	double cphi = cos(phi);
	double sphi = sin(phi);
	double cgam = cos(gamma);
	double sgam = sin(gamma);
	double qsum = 0;
	int i;
	for (i = 0; i < n; i++) {
		double x1i = (double) *((int *)PyArray_GETPTR2(a1,i,0));
		double y1i = (double) *((int *)PyArray_GETPTR2(a1,i,1));
		double x2i = (double) *((int *)PyArray_GETPTR2(a2,i,0));
		double y2i = (double) *((int *)PyArray_GETPTR2(a2,i,1));

		double fx = ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * cphi
		          + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * sphi + a2x0;

		double fy = -((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * sphi
		           + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * cphi + a2y0;

		qsum += sqrt((x2i - fx) * (x2i - fx) + (y2i - fy) * (y2i - fy));
	}
	return qsum;
};
*/

/*
**
** Least Square Fit Tilt Parameters
**
*/

static PyObject* willsq(PyObject *self, PyObject *args) {
/*
	float *x, float *y, float *xs, float *ys,
	int n, float thetaw, float * gammaw, float * phiw)
*/
	PyObject *a1, *a2;
	PyObject *pynull = PyInt_FromLong(0);
	double phi0, gamma0, theta0;
	double phi, gamma;
	double eps;
	if (!PyArg_ParseTuple(args, "OOfff", &a1, &a2, &theta0, &gamma0, &phi0))
		return pynull;

	int n = MIN(PyArray_DIMS(a1)[0], PyArray_DIMS(a2)[0]);
	if (n < 3)
		return pynull;


	double *aval, *x2diff, *y2diff;
	if (
		((aval   = (double *) malloc(n * 4 * sizeof(double))) == (double *) NULL) ||
		((x2diff = (double *) malloc(n *	   sizeof(double))) == (double *) NULL) ||
		((y2diff = (double *) malloc(n *	   sizeof(double))) == (double *) NULL)
	)
		return pynull;

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

	double a1x0 = (double) *((int *)PyArray_GETPTR2(a1,15,0));
	double a1y0 = (double) *((int *)PyArray_GETPTR2(a1,15,1));
	double a2x0 = (double) *((int *)PyArray_GETPTR2(a2,15,0));
	double a2y0 = (double) *((int *)PyArray_GETPTR2(a2,15,1));


	double sqa[4][5], sqb[4][4], r[4];
	int iter = 0;
	double check = 1.0;
	double qxsum, qysum;	
	while (check > 0.0000005 && iter < 2000) {
		iter++;
		int i,l,k;
		qxsum = 0;
		qysum = 0;

		/* Build system of normal equations build matrice A, calculate x2diff */
		for (i = 0; i < n; i++) {
			double x1i = (double) *((int *)PyArray_GETPTR2(a1,i,0));
			double y1i = (double) *((int *)PyArray_GETPTR2(a1,i,1));
			double x2i = (double) *((int *)PyArray_GETPTR2(a2,i,0));
			//double y2i = (double) *((int *)PyArray_GETPTR2(a2,i,1));
			double fx = ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * cphi
				        + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * sphi + a2x0;
			x2diff[i] = x2i - fx;
			//printf("x2r = %.1f, x2c = %.1f, diff = %.1f\n",x2i,fx,x2diff[i]);  
			qxsum += x2diff[i] * x2diff[i];
			aval[i*4] = 1.0;
			/* Ai2: */
			aval[i*4+1] = 0.0;
			/* Ai3: */
			aval[i*4+2] = 
				- ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * sphi * cthe
				+ ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * cphi;
			/* Ai4: */
			aval[i*4+3] =
				( -(x1i - a1x0) * sgam - (y1i - a1y0) * cgam) * cthe * cphi
				+ ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * sphi;
		}

		/* Calculate square matrice Aki * Ail	*/
		for (l = 0; l < 4; l++) {
			for (k = 0; k < 4; k++) {
				sqa[k][l] = 0.0;
				for (i = 0; i < n; i++)
					sqa[k][l] += aval[i*4+k] * aval[i*4+l];
				//printf("sqa[%d][%d] = %.1f\n",k,l,sqa[k][l]);
			}
		}

		/* Calculate first part of left side of normal equation */
		for (k = 0; k < 4; k++) {
			r[k] = 0.0;
			for (i = 0; i < n; i++)
				r[k] += aval[i*4+k] * x2diff[i];
		}

		/*  Build matrice B, calculate y2diff */
		for (i = 0; i < n; i++) {
			double x1i = (double) *((int *)PyArray_GETPTR2(a1,i,0));
			double y1i = (double) *((int *)PyArray_GETPTR2(a1,i,1));
			//double x2i = (double) *((int *)PyArray_GETPTR2(a2,i,0));
			double y2i = (double) *((int *)PyArray_GETPTR2(a2,i,1));
			double fy = -((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * sphi
			           + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * cphi + a2y0;
			y2diff[i]	  = y2i - fy;
			qysum	+= y2diff[i] * y2diff[i];
			aval[i*4+0] = 0.0;
			/* Bi2 */
			aval[i*4+1] = 1.0;
			/* Bi3 */
			aval[i*4+2] = 
				- ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cphi * cthe
				- ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * sphi;
			/* Bi4  */
			aval[i*4+3] = 
				-(-(x1i - a1x0) * sgam - (y1i - a1y0) * cgam) * cthe * sphi
				+ ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cphi;
		}

		/* Calculate square matrice Bki * Bil: */
		for (l = 0; l < 4; l++) {
			for (k = 0; k < 4; k++) {
				sqb[k][l] = 0.0;
				for (i = 0; i < n; i++)
					sqb[k][l] += aval[i*4+k] * aval[i*4+l];
				//printf("sqb[%d][%d] = %.1f\n",k,l,sqa[k][l]);
			}
		}

		/*  Calculate second part of left side of normal equation:  */
		for (k = 0; k < 4; k++) {
			for (i = 0; i < n; i++)
				r[k] += aval[i*4+k] * y2diff[i];
		}

		/*  Add SQA and SQB   */
		for (k = 0; k < 4; k++) {
			for (l = 0; l < 4; l++)
				sqa[k][l] += sqb[k][l];
		}

		eps = 0.0;
		for (i = 0; i < 4; i++)
			sqa[i][4] = r[i];

		/* What the hell is mircol? */
		if (mircol(4, 1, 5, sqa, eps, r) != 0 ) {
				printf("*** MIRCOL: Least Square Fit failed!\n*** Give more coordinates or better start values.\n");
				//return pynull;
		}

		a2x0 += r[0];
		a2y0 += r[1];
		rphi += r[2];
		rgam += r[3];

		phi	  = rphi * RAD2DEG;
		gamma = rgam * RAD2DEG;

		if (fabs(gamma) > 90 || fabs(phi) > 90) {
			printf("*** Least Square Fit failed!\n*** Give more coordinates or better start values.\n");
			//return pynull;
		}

		/* Determine accuracy of solution */
		cphi   = cos(rphi);
		sphi   = sin(rphi);
		cgam   = cos(rgam);
		sgam   = sin(rgam);
		for (i = 0; i < n; i++) {
			double x1i = (double) *((int *)PyArray_GETPTR2(a1,i,0));
			double y1i = (double) *((int *)PyArray_GETPTR2(a1,i,1));
			double x2i = (double) *((int *)PyArray_GETPTR2(a2,i,0));
			double y2i = (double) *((int *)PyArray_GETPTR2(a2,i,1));
			double fx = ((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * cphi
			          + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * sphi + a2x0;

			x2diff[i] = x2i - fx;
			qxsum += x2diff[i] * x2diff[i];

			double fy = -((x1i - a1x0) * cgam - (y1i - a1y0) * sgam) * cthe * sphi
			           + ((x1i - a1x0) * sgam + (y1i - a1y0) * cgam) * cphi + a2y0;

			y2diff[i] = y2i - fy;
			qysum += y2diff[i] * y2diff[i];
		}

		printf("Iter: %4d  Phi: %.2f, Gam: %.2f, Orig: (%.2f, %.2f)\n",iter,phi,gamma,a2x0,a2y0);
		printf("      dPhi: %.2f, dGam: %.2f, dOrig: (%.2f, %.2f)\n",r[2]*RAD2DEG,r[3]*RAD2DEG,r[0],r[1]);
		printf("      Qxsum: %f  Qysum: %f\n",qxsum,qysum);

		check = fabs(r[0]) + fabs(r[1]) + fabs(r[2]*RAD2DEG) + fabs(r[3]*RAD2DEG);

	} /* END ITER LOOP */

	if (aval) {free(aval); aval = (double *) NULL;}
	if (x2diff) {free(x2diff); x2diff = (double *) NULL;}
	if (y2diff) {free(y2diff); y2diff = (double *) NULL;}

	PyObject *result = PyDict_New();

	PyObject *pyphi = PyFloat_FromDouble((double) phi);
	PyDict_SetItemString(result, "phi", pyphi);
	Py_DECREF(pyphi);

	PyObject *pygamma = PyFloat_FromDouble((double) gamma);
	PyDict_SetItemString(result, "gamma", pygamma);
	Py_DECREF(pygamma);

	PyObject *pycheck = PyFloat_FromDouble((double) check);
	PyDict_SetItemString(result, "check", pycheck);
	Py_DECREF(pycheck);

	PyObject *pyqxsum = PyFloat_FromDouble((double) qxsum);
	PyDict_SetItemString(result, "qxsum", pyqxsum);
	Py_DECREF(pyqxsum);

	PyObject *pyqysum = PyFloat_FromDouble((double) qysum);
	PyDict_SetItemString(result, "qysum", pyqysum);
	Py_DECREF(pyqysum);

	PyObject *pya2x0 = PyFloat_FromDouble((double) a2x0);
	PyDict_SetItemString(result, "a2x0", pya2x0);
	Py_DECREF(pya2x0);

	PyObject *pya2y0 = PyFloat_FromDouble((double) a2y0);
	PyDict_SetItemString(result, "a2y0", pya2y0);
	Py_DECREF(pya2y0);

	Py_DECREF(pynull);

	return result;

};



/*
**
** Tilt Angle Calculator
**
*/

static PyObject* tiltang(PyObject *self, PyObject *args) {
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
	double wtot=0, wsum=0;
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
				double weight = (area1 + area2) / arealim;
				sum += theta;
				wsum += theta*weight;
				wtot += weight;
				sumsq += (theta*theta);
				numtri++;
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
		//printf("top = %.5f\n", top);
		thetadev = 0;
	} else
		thetadev = sqrt( top / (numtri * (numtri - 1.0)) );
	
	theta = theta * RAD2DEG;
	wtheta = wtheta * RAD2DEG;
	thetadev = thetadev * RAD2DEG;

	/* Convert results into python dictionary */

	PyObject *result = PyDict_New();

	PyObject *pytheta = PyFloat_FromDouble((double) theta);
	PyDict_SetItemString(result, "theta", pytheta);
	Py_DECREF(pytheta);

	PyObject *pywtheta = PyFloat_FromDouble((double) wtheta);
	PyDict_SetItemString(result, "wtheta", pywtheta);
	Py_DECREF(pywtheta);

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

static struct PyMethodDef numeric_methods[] = {
	{"tiltang", tiltang, METH_VARARGS},
	{"willsq", willsq, METH_VARARGS},
	{NULL, NULL}
};

void initradermacher() {
	(void) Py_InitModule("radermacher", numeric_methods);
	import_array();
}




