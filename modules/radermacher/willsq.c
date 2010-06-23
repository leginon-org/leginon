#include "main.h"


/*
**
** Least Square Fit Tilt Parameters
**
*/


PyObject* willsq(PyObject *self, PyObject *args) {
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


