#include <Python.h>
#include <Numeric/arrayobject.h>
#include <math.h>

/******************************************
 statistical functions
******************************************/

#undef min
#undef max

/****
Note from Jim about min(), max(), etc.:  It would be nice to do these 
more in the style of argmin and argmax in Numeric's multiarraymodule.c 
so that there are actually several type specific functions instead of 
simply casting to floats all the time.  It would also be nice to use
their style because there is a lot of repetitive code here that could
be cleaned up by using macros like they did.
****/
static PyObject *
min(PyObject *self, PyObject *args)
{
	PyObject *input;
	PyArrayObject *inputarray;
	float *iter;
	float result;
	int len, i;

	if (!PyArg_ParseTuple(args, "O", &input))
		return NULL;

	/* create proper PyArrayObjects from input source */
	inputarray = (PyArrayObject *)
		PyArray_ContiguousFromObject(input, PyArray_FLOAT, 1, 0);
	if (inputarray == NULL) return NULL;

	len = PyArray_Size((PyObject *)inputarray);

	iter = (float *)inputarray->data;
	result = *iter;
	iter++;
	for(i=1; i<len; i++) {
		if (*iter < result) {
			result = *iter;
		}
		iter++;
	}

	Py_DECREF(inputarray);

	return Py_BuildValue("f", result);
}

static PyObject *
max(PyObject *self, PyObject *args)
{
	PyObject *input;
	PyArrayObject *inputarray;
	float *iter;
	float result;
	int len, i;

	if (!PyArg_ParseTuple(args, "O", &input))
		return NULL;

	/* create proper PyArrayObjects from input source */
	inputarray = (PyArrayObject *)
		PyArray_ContiguousFromObject(input, PyArray_FLOAT, 1, 0);
	if (inputarray == NULL) return NULL;

	len = PyArray_Size((PyObject *)inputarray);

	iter = (float *)inputarray->data;
	result = *iter;
	iter++;
	for(i=1; i<len; i++) {
		if (*iter > result) {
			result = *iter;
		}
		iter++;
	}

	Py_DECREF(inputarray);

	return Py_BuildValue("f", result);
}

/****
The minmax function calculates both min and max of an array in one loop.
It is faster than the sum of both min and max above because it does
3 comparisons for every 2 elements, rather than two comparison for every 
element
****/

static PyObject *
minmax(PyObject *self, PyObject *args)
{
	PyObject *input;
	PyArrayObject *inputarray;
	float *iter;
	float minresult, maxresult;
	int len, i;

	if (!PyArg_ParseTuple(args, "O", &input))
		return NULL;

	/* create proper PyArrayObjects from input source */
	inputarray = (PyArrayObject *)
		PyArray_ContiguousFromObject(input, PyArray_FLOAT, 1, 0);
	if (inputarray == NULL) return NULL;

	len = PyArray_Size((PyObject *)inputarray);

	iter = (float *)inputarray->data;
	if(len % 2) {
		/* odd length:  initial min and max are first element */
		minresult = maxresult = *iter;
		iter += 1;
		len -= 1;
	} else {
		/* even length:  min and max from first two elements */
		if (iter[0] > iter[1]) {
			maxresult = iter[0];
			minresult = iter[1];
		} else {
			maxresult = iter[1];
			minresult = iter[0];
		}
		iter += 2;
		len -= 2;
	}

	for(i=0; i<len; i+=2) {
		if (iter[0] > iter[1]) {
			if (iter[0] > maxresult) maxresult=iter[0];
			if (iter[1] < minresult) minresult=iter[1];
		} else {
			if (iter[1] > maxresult) maxresult=iter[1];
			if (iter[0] < minresult) minresult=iter[0];
		}
		iter += 2;
	}

	Py_DECREF(inputarray);

	return Py_BuildValue("ff", minresult, maxresult);
}

float sum_FLOAT(float *array, int len) {
	float *ptr=array;
	double result=0.0;
	int i;

	for(i=0; i<len; i++,ptr++) {
		result += *ptr;
	}
	/* double -> float? */
	return result;
}

float sum_squares_FLOAT(float *array, int len) {
	float *ptr=array;
	double result=0.0;
	int i;

	for(i=0; i<len; i++,ptr++) {
		result += (*ptr)*(*ptr);
	}
	/* double -> float? */
	return result;
}

float mean_FLOAT(float *array, int len) {
	double result;

	result = sum_FLOAT(array, len);
	result /= (float)len;
	/* double -> float? */
	return result;
}

float standard_deviation_FLOAT(float *array, int len, int know_mean, float mean) {
	double m, sumsquares, result;

	sumsquares = sum_squares_FLOAT(array, len);
	if(know_mean) {
		m = mean;
	} else {
		m = mean_FLOAT(array, len);
	}
	result = sqrt(sumsquares / (float)len - m*m);
	/* double -> float? */
	return result;
}

static PyObject *
stdev(PyObject *self, PyObject *args)
{
	PyObject *input, *meanobject;
	PyArrayObject *inputarray;
	int len;
	float result, mean;
	int have_mean;

	meanobject = Py_None;
	if (!PyArg_ParseTuple(args, "O|f", &input, &meanobject))
		return NULL;

	if (meanobject == Py_None) {
		have_mean = 0;
		mean = 0.0;
	} else {
		have_mean = 1;
		mean = (float)PyFloat_AsDouble(meanobject);
	}

	/* create proper PyArrayObjects from input source */
	inputarray = (PyArrayObject *)
		PyArray_ContiguousFromObject(input, PyArray_FLOAT, 1, 0);
	if (inputarray == NULL) return NULL;

	len = PyArray_Size((PyObject *)inputarray);
	result = standard_deviation_FLOAT((float *)inputarray->data, len, have_mean, mean);

	Py_DECREF(inputarray);

	return Py_BuildValue("f", result);
}


/*******************
blob finder stuff
*******************/

/*
  25000 is about the limit on bnc16 where I tested it
  more than that causes seg fault, probably from too much recursion
*/
#define BLOBLIMIT 25000

int add_blob_point(PyArrayObject *image, PyArrayObject *map, PyObject *pixelrow, PyObject *pixelcol, PyObject *pixelv, int row, int col) {
	/* delete this point from map */
	int *map_ptr;
	int rows, cols, r, c;
	int index;

	map_ptr = (int *)map->data;
	rows = map->dimensions[0];
	cols = map->dimensions[1];
	index = row*rows+col;

	/* reset this pixel in the map */
	map_ptr[index] = 0;
	/* add to the blob lists */
	PyList_Append(pixelrow, PyInt_FromLong(row));
	PyList_Append(pixelcol, PyInt_FromLong(col));

	if(image->descr->type_num == PyArray_FLOAT) {
		PyList_Append(pixelv, PyFloat_FromDouble(((float *)image->data)[index]));
	} else if(image->descr->type_num == PyArray_DOUBLE) {
		PyList_Append(pixelv, PyFloat_FromDouble(((double *)image->data)[index]));
	}

	if (PyList_Size(pixelrow) > BLOBLIMIT) {
		/* return int? */
		return;
	}

	/* rercursively run this on neighbors */
	for(r=row-1; r<row+2; r++) {
		if(r < 0 || r >= rows) continue;
		for(c=col-1; c<col+2; c++) {
			if(c < 0 || c >= cols) continue;
			if(map_ptr[r*rows+c])
				add_blob_point(image, map, pixelrow, pixelcol, pixelv, r, c);
		}
	}
	/* return int? */
}

static PyObject *
blobs(PyObject *self, PyObject *args)
{
	PyArrayObject *inputmap, *map, *image;
	PyObject *results, *newblob, *pixelrow, *pixelcol, *pixelv;
	int rows, cols, r, c, len;
	int *map_ptr;
	int i, size;

	if (!PyArg_ParseTuple(args, "O!O!", &PyArray_Type, &image, &PyArray_Type, &inputmap))
		return NULL;

	/* must be 2-d integer array */
	if (image->nd != 2) {
		PyErr_SetString(PyExc_ValueError, "image array must be two-dimensional");
		return NULL;
	}
	if (inputmap->nd != 2) {
		PyErr_SetString(PyExc_ValueError, "map must be two-dimensional");
		return NULL;
	}

	/* create a contiguous bit map from input map */
	map = (PyArrayObject *)
		PyArray_ContiguousFromObject((PyObject *)inputmap, PyArray_INT, 2, 2);
	if (map == NULL) return NULL;

	rows = map->dimensions[0];
	cols = map->dimensions[1];
	len = rows*cols;

	results = PyList_New(0);

	map_ptr = (int *)map->data;
	for(r=0; r<rows; r++) {
		for(c=0; c<cols; c++) {
			if(*map_ptr) {
				/* new blob */
				newblob = PyDict_New();
				pixelrow = PyList_New(0);
				pixelcol = PyList_New(0);
				pixelv = PyList_New(0);
				PyDict_SetItemString(newblob, "pixelrow", pixelrow);
				PyDict_SetItemString(newblob, "pixelcol", pixelcol);
				PyDict_SetItemString(newblob, "pixelv", pixelv);
				if (newblob == NULL) return NULL;

				/* find all points in blob */
				add_blob_point(image, map, pixelrow, pixelcol, pixelv, r, c);

				/* append blob to our results */
				if (PyList_Append(results, newblob)) {
					Py_DECREF(newblob);
					return NULL;
				}
				/*
				size = PyList_Size(newblob);
				for(i = 0; i < size; i++)
					Py_DECREF(PyList_GetItem(newblob, i));
				*/
				Py_DECREF(newblob);
				size = PyList_Size(pixelrow);
				for(i = 0; i < size; i++)
					Py_DECREF(PyList_GetItem(pixelrow, i));
				Py_DECREF(pixelrow);
				size = PyList_Size(pixelcol);
				for(i = 0; i < size; i++)
					Py_DECREF(PyList_GetItem(pixelcol, i));
				Py_DECREF(pixelcol);
				size = PyList_Size(pixelv);
				for(i = 0; i < size; i++)
					Py_DECREF(PyList_GetItem(pixelv, i));
				Py_DECREF(pixelv);
			}
			map_ptr++;
		}
	}

	Py_DECREF(map);

	return results;
}

int despike_FLOAT(float *array, int rows, int cols, int statswidth, float ztest) {
	float *newptr, *oldptr, *rowptr, *colptr;
	int sw2, sw2cols, sw2cols_sw2, sw2cols__sw2;
	int r, c, rr, cc;
	int spikes=0;
	float mean, std, nn, ppm;
	float sum, sum2;

	sw2 = statswidth / 2;
	nn = (float)statswidth * statswidth - 1;

	/* pointer delta to last row of neighborhood */
	sw2cols = sw2 * cols;
	/* pointer delta to first column of neighborhood */
	sw2cols_sw2 = -sw2cols - sw2;
	/* pointer delta to first column after neighborhood */
	sw2cols__sw2 = -sw2cols + sw2 + 1;

	/* iterate to each pixel, despike, then update stats box */
	rowptr = array + sw2cols;
	for(r=sw2; r<rows-sw2; r++) {
		colptr = rowptr + sw2;

		/* initialize stats box sum and sum2 */
		sum = sum2 = 0.0;
		newptr = rowptr - sw2cols;
		for(rr=0; rr<statswidth; rr++) {
			for(cc=0; cc<statswidth; cc++) {
				sum += newptr[cc];
				sum2 += newptr[cc] * newptr[cc];
			}
			newptr += cols;
		}
		sum -= *colptr;
		sum2 -= (*colptr) * (*colptr);

		for(c=sw2; c<cols-sw2; c++) {
			/* finalize stats and despike this pixel */
			mean = sum / nn;
			/* double -> float? */
			std = sqrt(sum2/nn - mean*mean);
			if(fabs(*colptr-mean) > (ztest*std)) {
				*colptr = mean;
				spikes++;
			}
			/* we were excluding center, so put it back in */
			sum += *colptr;
			sum2 += (*colptr) * (*colptr);

			/* update stats box sum and sum2 */
			/* remove old column, add new column */
			oldptr = colptr + sw2cols_sw2;
			newptr = colptr + sw2cols__sw2;
			for(rr=0; rr<statswidth; rr++) {
				sum -= *oldptr;
				sum2 -= *oldptr * *oldptr;
				sum += *newptr;
				sum2 += *newptr * *newptr;
				oldptr += cols;
				newptr += cols;
			}
			colptr++;
			sum -= *colptr;
			sum2 -= (*colptr) * (*colptr);
		}
		/* advance to next row */
		rowptr += cols;
	}
	/* double -> float? */
	return spikes;
}

static PyObject *
despike(PyObject *self, PyObject *args)
{
	PyArrayObject *image, *floatimage;
	int rows, cols, size, debug;
	float ztest;
	int spikes, ppm;

	if (!PyArg_ParseTuple(args, "O!ifi", &PyArray_Type, &image, &size, &ztest, &debug))
		return NULL;

	/* must be 2-d array */
	if (image->nd != 2) {
		PyErr_SetString(PyExc_ValueError, "image array must be two-dimensional");
		return NULL;
	}

	/* create a contiguous float image from input image */
	floatimage = (PyArrayObject *)
		PyArray_ContiguousFromObject((PyObject *)image, PyArray_FLOAT, 2, 2);
	if (floatimage == NULL) return NULL;

	rows = floatimage->dimensions[0];
	cols = floatimage->dimensions[1];

	spikes = despike_FLOAT((float *)(floatimage->data), rows, cols, size, ztest);
	ppm = 1000000 * spikes / (rows * cols);
	if(debug) printf("despike ppm:  %d\n", ppm);

	return PyArray_Return(floatimage);
}

static PyObject *
bin(PyObject *self, PyObject *args)
{
	PyArrayObject *image, *floatimage, *result;
	int binsize, rows, cols, newdims[2];
	float *original, *resultrow, *resultpixel;
	int i, j, ib, jb;
	int reslen, resrows, rescols, n;
	char errstr[80];

	if (!PyArg_ParseTuple(args, "O!i", &PyArray_Type, &image, &binsize))
		return NULL;

	/* must be 2-d array */
	if (image->nd != 2) {
		PyErr_SetString(PyExc_ValueError, "image array must be two-dimensional");
		return NULL;
	}

	/* must be able to be binned by requested amount */
	rows = image->dimensions[0];
	cols = image->dimensions[1];
	if ((rows%binsize) || (cols%binsize) ) {
		sprintf(errstr, "bin by %d does not allow image dimensions %d,%d do not allow binning by %d", rows,cols,binsize);
		PyErr_SetString(PyExc_ValueError, errstr);
		return NULL;
	}

	/* create a contiguous float image from input image */
	floatimage = (PyArrayObject *)
		PyArray_ContiguousFromObject((PyObject *)image, PyArray_FLOAT, 2, 2);
	if (floatimage == NULL) return NULL;


	/* create a float image for result */
	resrows = rows / binsize;
	rescols = cols / binsize;
	newdims[0] = resrows;
	newdims[1] = rescols;
	result = (PyArrayObject *)PyArray_FromDims(2, newdims, PyArray_FLOAT);
	reslen = PyArray_Size((PyObject *)result);

	/* zero the result */
	resultpixel = (float *)result->data;
	for(i=0; i<reslen; i++) {
		*resultpixel = 0.0;
		resultpixel++;
	}

	/* calc sum of the bins */
	resultpixel = resultrow = (float *)result->data;
	original = (float *)floatimage->data;
	for(i=0; i<resrows; i++) {
		for(ib=0;ib<binsize;ib++) {
			resultpixel=resultrow;
			for(j=0; j<rescols; j++) {
				for(jb=0;jb<binsize;jb++) {
					*resultpixel += *original;
					original++;
				}
				resultpixel++;
			}
		}
		resultrow +=rescols;
	}

	/* calc mean of the bins */
	resultpixel = (float *)result->data;
	n = binsize * binsize;
	for(i=0; i<reslen; i++) {
		*resultpixel /= n;
		resultpixel++;
	}

	Py_DECREF(floatimage);

	return PyArray_Return(result);
}

static PyObject *houghline2(PyObject *self, PyObject *args) {
	PyObject *input, *gradient = NULL;
	PyArrayObject *inputarray, *gradientarray, *hough;
	int dimensions[2];
	int n;
	int i, j, theta, r;
	double rtheta;
	double gradientvalue;
	float increment = 1.0;
	float gradient_tolerance = 1.0;
	float gradient_tolerances[2];

	if (!PyArg_ParseTuple(args, "OO|ff", &input, &gradient, &gradient_tolerance,
																				&increment))
		return NULL;

	inputarray = (PyArrayObject *)
									PyArray_ContiguousFromObject(input, PyArray_DOUBLE, 2, 2);
	gradientarray = (PyArrayObject *)
									PyArray_ContiguousFromObject(gradient, PyArray_DOUBLE, 2, 2);

	if(inputarray->dimensions[0] != inputarray->dimensions[1])
		return NULL;

	n = inputarray->dimensions[0];

	dimensions[0] = (int)ceil(M_SQRT2*n);
	dimensions[1] = (int)round(90.0/increment);
	hough = (PyArrayObject *)PyArray_FromDims(2, dimensions, PyArray_DOUBLE);

	for(i = 0; i < inputarray->dimensions[0]; i++)
		for(j = 0; j < inputarray->dimensions[1]; j++)
			if(((double *)inputarray->data)[j * (i + 1)] > 0.0) {
				gradientvalue = *(double *)(gradientarray->data
																		+ i*gradientarray->strides[0]
																		+ j*gradientarray->strides[1]);
				while(gradientvalue < 0.0)
					gradientvalue += 2.0*M_PI;
				while(gradientvalue > M_PI_2)
					gradientvalue -= M_PI;
				gradient_tolerances[0] = gradientvalue - gradient_tolerance*M_PI/180.0;
				gradient_tolerances[1] = gradientvalue + gradient_tolerance*M_PI/180.0;
				for(theta = 0; theta < dimensions[1]; theta++) {
					rtheta = theta * increment * M_PI/180;
					r = (int)(abs(j*cos(rtheta)) + i*sin(rtheta) + 0.5);
					if(rtheta > gradient_tolerances[0] && rtheta < gradient_tolerances[1])
					*(double *)(hough->data + r*hough->strides[0]
											+ theta*hough->strides[1]) +=
									*(double *)(inputarray->data + i*inputarray->strides[0]
															+ j*inputarray->strides[1]);
				}
			}

	return PyArray_Return(hough);
}

static PyObject *houghline(PyObject *self, PyObject *args) {
	PyObject *input, *gradient = NULL;
	PyArrayObject *inputarray, *gradientarray = NULL, *hough;
	int dimensions[2];
	int n;
	int i, j, k, kmin, kmax, r;
	double rtheta;
	double gradientvalue;
	int ntheta = 90;
	float gradient_tolerance = M_PI/180.0;

	if (!PyArg_ParseTuple(args, "O|Ofi", &input, &gradient, &gradient_tolerance,
																				&ntheta))
		return NULL;

	inputarray = (PyArrayObject *)
									PyArray_ContiguousFromObject(input, PyArray_DOUBLE, 2, 2);
	if(gradient != NULL)
		gradientarray = (PyArrayObject *)
									PyArray_ContiguousFromObject(gradient, PyArray_DOUBLE, 2, 2);

	if(inputarray->dimensions[0] != inputarray->dimensions[1])
		return NULL;

	n = inputarray->dimensions[0];

	dimensions[0] = (int)ceil(M_SQRT2*n);
	dimensions[1] = ntheta;
	hough = (PyArrayObject *)PyArray_FromDims(2, dimensions, PyArray_DOUBLE);

	for(i = 0; i < inputarray->dimensions[0]; i++)
		for(j = 0; j < inputarray->dimensions[1]; j++)
			if(((double *)inputarray->data)[j * (i + 1)] > 0.0) {
				if(gradientarray != NULL) {
					gradientvalue = *(double *)(gradientarray->data
																			+ i*gradientarray->strides[0]
																			+ j*gradientarray->strides[1]);
					while(gradientvalue < 0.0)
						gradientvalue += 2.0*M_PI;
					while(gradientvalue > M_PI_2)
						gradientvalue -= M_PI;
					if(gradientvalue < 0.0 || gradientvalue > M_PI_2)
						continue;
					kmin = (int)(ntheta/M_PI_2*(gradientvalue - gradient_tolerance)+0.5);
					kmax = (int)(ntheta/M_PI_2*(gradientvalue + gradient_tolerance)+1.5);
					if(kmin < 0)
						kmin = 0;
					if(kmax > dimensions[1])
						kmax = dimensions[1];
				} else {
					kmin = 0;
					kmax = dimensions[1];
				}
				for(k = kmin; k < kmax; k++) {
					rtheta = (k*M_PI_2)/ntheta;
					r = (int)(abs(j*cos(rtheta)) + i*sin(rtheta) + 0.5);
					*(double *)(hough->data + r*hough->strides[0]
											+ k*hough->strides[1]) +=
									*(double *)(inputarray->data + i*inputarray->strides[0]
															+ j*inputarray->strides[1]);
				}
			}

	return PyArray_Return(hough);
}

static struct PyMethodDef numeric_methods[] = {
	{"min", min, METH_VARARGS},
	{"max", max, METH_VARARGS},
	{"minmax", minmax, METH_VARARGS},
	{"stdev", stdev, METH_VARARGS},
	{"blobs", blobs, METH_VARARGS},
	{"despike", despike, METH_VARARGS},
	{"bin", bin, METH_VARARGS},
	{"houghline", houghline, METH_VARARGS},
	{NULL, NULL}
};

void initnumextension()
{
	(void) Py_InitModule("numextension", numeric_methods);
	import_array()
}
