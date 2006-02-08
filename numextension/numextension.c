#include <Python.h>
#include <numarray/libnumarray.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef M_PI_2
#define M_PI_2 1.57079632679489661923
#endif

#ifndef M_SQRT2
#define M_SQRT2 1.41421356237309504880
#endif

int PyArray_Size(PyArrayObject *input)
{
	int size, dims, i;
	size = 1.0;
	dims = input->nd;
	for(i=0;i<dims;i++)
	{
		size = size * input->dimensions[i];
	}
	return size;
}

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
	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	len = PyArray_Size(inputarray);

	iter = (float *)inputarray->data;
	result = *iter;
	iter++;
	for(i=1; i<len; i++) {
		if (*iter < result) {
			result = *iter;
		}
		iter++;
	}

	Py_XDECREF(inputarray);

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
	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	len = PyArray_Size(inputarray);

	iter = (float *)inputarray->data;
	result = *iter;
	iter++;
	for(i=1; i<len; i++) {
		if (*iter > result) {
			result = *iter;
		}
		iter++;
	}

	Py_XDECREF(inputarray);

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
	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	len = PyArray_Size(inputarray);

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

	Py_XDECREF(inputarray);

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
	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	len = PyArray_Size(inputarray);
	result = standard_deviation_FLOAT((float *)inputarray->data, len, have_mean, mean);

	Py_XDECREF(inputarray);

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

int add_blob_point(PyArrayObject *map, PyObject *pixelrow, PyObject *pixelcol, PyObject *pixelv, int row, int col) {
	/* delete this point from map */
	int *map_ptr;
	int rows, cols, r, c;
	int index;

	map_ptr = (int *)map->data;
	rows = map->dimensions[0];
	cols = map->dimensions[1];
	index = row*cols+col;

	/* reset this pixel in the map */
	map_ptr[index] = 0;
	/* add to the blob lists */
	PyList_Append(pixelrow, PyInt_FromLong(row));
	PyList_Append(pixelcol, PyInt_FromLong(col));

	if (PyList_Size(pixelrow) > BLOBLIMIT) {
		/* return int? */
		return;
	}

	/* rercursively run this on neighbors */
	for(r=row-1; r<row+2; r++) {
		if(r < 0 || r >= rows) continue;
		for(c=col-1; c<col+2; c++) {
			if(c < 0 || c >= cols) continue;
			if(map_ptr[r*cols+c])
				add_blob_point(map, pixelrow, pixelcol, pixelv, r, c);
		}
	}
	/* return int? */
}

static PyObject *
blobs(PyObject *self, PyObject *args)
{
	PyArrayObject *inputmap, *map;
	PyObject *results, *newblob, *pixelrow, *pixelcol, *pixelv;
	int rows, cols, r, c, len;
	int *map_ptr;
	int i, size;

	if (!PyArg_ParseTuple(args, "O", &inputmap))
		return NULL;

	/* must be 2-d integer array */
	if (inputmap->nd != 2) {
		PyErr_SetString(PyExc_ValueError, "map must be two-dimensional");
		return NULL;
	}

	/* create a contiguous bit map from input map */
	map = NA_InputArray(inputmap, tInt32, NUM_C_ARRAY|NUM_COPY);
	if (map == NULL) {
		Py_XDECREF(map);
		return NULL;
	}

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
				add_blob_point(map, pixelrow, pixelcol, pixelv, r, c);

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

	Py_XDECREF(map);

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
	int spikes;
	float ppm;

	if (!PyArg_ParseTuple(args, "Oifi", &image, &size, &ztest, &debug))
		return NULL;

	/* must be 2-d array */
	if (image->nd != 2) {
		PyErr_SetString(PyExc_ValueError, "image array must be two-dimensional");
		return NULL;
	}

	/* create an array object copy of input data */
	floatimage = NA_IoArray(image, tFloat32, NUM_C_ARRAY);
	if (floatimage == NULL) {
		Py_XDECREF(floatimage);
		return NULL;
	}

	rows = floatimage->dimensions[0];
	cols = floatimage->dimensions[1];

	spikes = despike_FLOAT((float *)(floatimage->data), rows, cols, size, ztest);
	ppm = 1000000.0 * spikes / (rows * cols);
	if(debug) printf("spikes: %d, ppm: %.1f\n", spikes, ppm);

	Py_XDECREF(floatimage);
	Py_INCREF(Py_None);
	return Py_None;
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

	if (!PyArg_ParseTuple(args, "Oi", &image, &binsize))
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
	floatimage = NA_InputArray(image, tFloat32, NUM_C_ARRAY);
	if (floatimage == NULL) return NULL;


	/* create a float image for result */
	resrows = rows / binsize;
	rescols = cols / binsize;
	newdims[0] = resrows;
	newdims[1] = rescols;
	result = NA_vNewArray(NULL, tFloat32, 2, newdims);
	reslen = PyArray_Size(result);

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

	return NA_OutputArray(result, tFloat32, 0);
}

static PyObject *nonmaximasuppress(PyObject *self, PyObject *args) {
	PyObject *input, *gradient;
	PyArrayObject *inputarray, *gradientarray;
	int window = 7;
	int i, j, k;
	double m, theta, sintheta, costheta;

	if(!PyArg_ParseTuple(args, "OO|i", &input, &gradient, &window))
		return NULL;

	inputarray = NA_InputArray(input, tFloat64, NUM_C_ARRAY|NUM_COPY);
	gradientarray = NA_InputArray(gradient, tFloat64, NUM_C_ARRAY|NUM_COPY);

	for(i = 0; i < inputarray->nd; i++)
		if(inputarray->dimensions[i] != gradientarray->dimensions[i])
			return NULL;

	for(i = window/2; i < inputarray->dimensions[0] - window/2; i++) {
		for(j = window/2; j < inputarray->dimensions[1] - window/2; j++) {
			m = *(double *)(inputarray->data + i*inputarray->strides[0]
																				+ j*inputarray->strides[1]);
			theta = *(double *)(gradientarray->data + i*gradientarray->strides[0]
																							+ j*gradientarray->strides[1]);
			sintheta = sin(theta);
			costheta = cos(theta);
			for(k = -window/2; k <= window/2; k++) {
				if(m < *(double *)(inputarray->data
													+ (i + (int)(k*sintheta + 0.5))*inputarray->strides[0]
													+ (j + (int)(k*costheta + 0.5))*inputarray->strides[1]))
					*(double *)(inputarray->data + i*inputarray->strides[0]
																				+ j*inputarray->strides[1]) = 0.0;
			}
		}
	}
	Py_DECREF(inputarray);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *hysteresisthreshold(PyObject *self, PyObject *args) {
	PyObject *input;
	PyArrayObject *inputarray, *outputarray;
	int i, j, k, l;
	float lowthreshold, highthreshold;

	if(!PyArg_ParseTuple(args, "Off", &input, &lowthreshold, &highthreshold))
		return NULL;

	inputarray = NA_InputArray(input, tFloat64, NUM_C_ARRAY|NUM_COPY);
	outputarray = NA_vNewArray(NULL, tInt32, 2, inputarray->dimensions);

	for(i = 1; i < inputarray->dimensions[0] - 1; i++) {
		for(j = 1; j < inputarray->dimensions[1] - 1; j++) {
			if(*(double *)(inputarray->data + i*inputarray->strides[0]
											+ j*inputarray->strides[1]) >= highthreshold) {
				*(int *)(outputarray->data + i*outputarray->strides[0]
																		+ j*outputarray->strides[1]) = 1;
				for(k = -1; k <= 1; k++) {
					for(l = -1; l <= 1; l++) {
						if(k == 0 && l == 0)
							continue;
						if(*(double *)(inputarray->data
													+ (i + k)*inputarray->strides[0]
													+ (j + l)*inputarray->strides[1]) >= lowthreshold) {
							*(int *)(outputarray->data + (i + k)*outputarray->strides[0]
																				+ (j + l)*outputarray->strides[1]) = 1;
						}
					}
				}
			}
		}
	}
	Py_DECREF(inputarray);
	return NA_OutputArray(outputarray, tInt32, 0);
}

static PyObject *houghline(PyObject *self, PyObject *args) {
	PyObject *input, *gradient = NULL;
	PyArrayObject *inputarray, *gradientarray = NULL, *hough;
	int dimensions[3];
	int n, nd;
	int i, j, k, kmin, kmax, r, direction;
	double rtheta;
	double gradientvalue;
	int ntheta = 90;
	float gradient_tolerance = M_PI/180.0, rscale = 1.0;

	if(!PyArg_ParseTuple(args, "O|Ofif", &input, &gradient, &gradient_tolerance,
																				&ntheta, &rscale))
		return NULL;

	inputarray = NA_InputArray(input, tFloat64, NUM_C_ARRAY|NUM_COPY);
	if(gradient != NULL)
		gradientarray = NA_InputArray(gradient, tFloat64, NUM_C_ARRAY|NUM_COPY);

	if(inputarray->dimensions[0] != inputarray->dimensions[1])
		return NULL;

	n = inputarray->dimensions[0];

	dimensions[0] = (int)ceil(M_SQRT2*n) * rscale;
	dimensions[1] = ntheta;
	dimensions[2] = 2;
	if(gradientarray == NULL)
		nd = 2;
	else
		nd = 3;
	hough = NA_vNewArray(NULL, tFloat64, 3, dimensions);

	for(i = 0; i < inputarray->dimensions[0]; i++)
		for(j = 0; j < inputarray->dimensions[1]; j++)
			if(((double *)inputarray->data)[j * (i + 1)] > 0.0) {
				if(gradientarray != NULL) {
					gradientvalue = *(double *)(gradientarray->data
																			+ i*gradientarray->strides[0]
																			+ j*gradientarray->strides[1]);
					while(gradientvalue < 0.0)
						gradientvalue += 2.0*M_PI;
					while(gradientvalue >= 2.0*M_PI)
						gradientvalue -= 2.0*M_PI;
					if(gradientvalue >= 0.0 && gradientvalue < M_PI_2) {
						direction = 0;
					} else if	(gradientvalue >= M_PI && gradientvalue < 1.5*M_PI) {
						direction = 1;
						gradientvalue -= M_PI;
					} else {
						continue;
					}
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
					r = (int)((abs(j*cos(rtheta)) + i*sin(rtheta))*rscale + 0.5);
					*(double *)(hough->data + r*hough->strides[0]
											+ k*hough->strides[1]
											+ direction*hough->strides[2]) +=
									*(double *)(inputarray->data + i*inputarray->strides[0]
															+ j*inputarray->strides[1]);
				}
			}
	Py_DECREF(inputarray);
	Py_DECREF(gradientarray);

	return NA_OutputArray(hough, tFloat64, 0);
}

void getrange(PyArrayObject *array, float *minresult, float *maxresult) {
	int length, i;
	float *iter;

	length = PyArray_Size(array);

	iter = (float *)array->data;
	if(length % 2) {
		/* odd length:  initial min and max are first element */
		*minresult = *maxresult = *iter;
		iter += 1;
		length -= 1;
	} else {
		/* even length:  min and max from first two elements */
		if(iter[0] > iter[1]) {
			*maxresult = iter[0];
			*minresult = iter[1];
		} else {
			*maxresult = iter[1];
			*minresult = iter[0];
		}
		iter += 2;
		length -= 2;
	}

	for(i = 0; i < length; i += 2) {
		if(iter[0] > iter[1]) {
			if(iter[0] > *maxresult) *maxresult = iter[0];
			if(iter[1] < *minresult) *minresult = iter[1];
		} else {
			if(iter[1] > *maxresult) *maxresult = iter[1];
			if(iter[0] < *minresult) *minresult = iter[0];
		}
		iter += 2;
	}
}

static PyObject *linearscale(PyObject *self, PyObject *args) {
	PyObject *input;
	PyArrayObject *inputarray, *outputarray;
	int i, j;
	float frommin, frommax, fromrange, scale, value;

	if(!PyArg_ParseTuple(args, "Off", &input, &frommin, &frommax))
		return NULL;

	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY|NUM_COPY);

	/*getrange(inputarray, &frommin, &frommax);*/
	fromrange = frommax - frommin;
	if(fromrange == 0.0)
		scale = 0.0;
	else
		scale = 255.0/fromrange;

	outputarray = NA_vNewArray(NULL, tUInt8, 2, inputarray->dimensions);

	for(i = 0; i < inputarray->dimensions[0]; i++) {
		for(j = 0; j < inputarray->dimensions[1]; j++) {
			value = *(float *)(inputarray->data
												+ i*inputarray->strides[0] + j*inputarray->strides[1]);
			if(value <= frommin) {
				*(unsigned char *)(outputarray->data + i*outputarray->strides[0] + j*outputarray->strides[1]) = 0;
			} else if(value >= frommax) {
				*(unsigned char *)(outputarray->data + i*outputarray->strides[0] + j*outputarray->strides[1]) = 255;
			} else {
				*(unsigned char *)(outputarray->data + i*outputarray->strides[0] + j*outputarray->strides[1]) = (unsigned char)(scale*(value - frommin));
			}
		}
	}

	return NA_OutputArray(outputarray, tUInt8, 0);
}

static PyObject *rgbstring(PyObject *self, PyObject *args) {
	PyObject *input, *output, *colormap = NULL, *values = NULL, *cvalue = NULL;
	PyArrayObject *inputarray;
	int i, j, size;
	float frommin, frommax, fromrange, scale, value;
	unsigned char *string, *index;
	int scaledvalue;
	float colors = 255.0;
	unsigned char *rgb = NULL;

	if(!PyArg_ParseTuple(args, "Off|O", &input, &frommin, &frommax, &colormap))
		return NULL;

	if(colormap != NULL) {
		colors = (float)(PySequence_Size(colormap) - 1);
		rgb = PyMem_New(unsigned char, colors*3);
		for(i = 0; i <= colors; i++) {
			values = PySequence_Fast_GET_ITEM(colormap, i);
			for(j = 0; j < 3; j++) {
				cvalue = PySequence_Fast_GET_ITEM(values, j);
				rgb[i*3 + j] = (unsigned char)PyInt_AsUnsignedLongMask(cvalue);
			}
		}
	}

	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY|NUM_COPY);

/*	getrange(inputarray, &frommin, &frommax); */
	fromrange = frommax - frommin;
	if(fromrange == 0.0)
		scale = 0.0;
	else
		scale = (float)colors/fromrange;

	size = inputarray->dimensions[0]*inputarray->dimensions[1]*3;
	output = PyString_FromStringAndSize(NULL, size);
	index = PyString_AsString(output);
	for(i = 0; i < inputarray->dimensions[0]; i++) {
		for(j = 0; j < inputarray->dimensions[1]; j++) {
			value = *(float *)(inputarray->data
												+ i*inputarray->strides[0] + j*inputarray->strides[1]);
			
			if(value <= frommin) {
				scaledvalue = 0;
			} else if(value >= frommax) {
				scaledvalue = colors;
			} else {
				scaledvalue = (int)(scale*(value - frommin));
			}
			if(colormap == NULL) {
				*index = (unsigned char)scaledvalue;
				*(index + 1) = (unsigned char)scaledvalue;
				*(index + 2) = (unsigned char)scaledvalue;
			} else {
				scaledvalue *= 3;
				*index = rgb[scaledvalue];
				*(index + 1) = rgb[scaledvalue + 1];
				*(index + 2) = rgb[scaledvalue + 2];
			}
			index += 3;
		}
	}
	//PyMem_Del(rgb);

	Py_DECREF(inputarray);

	return output;
}

static PyObject *hanning(PyObject *self, PyObject *args, PyObject *kwargs) {
	PyObject *shape;
	int m, n;
	float a = 0.5, b;
	PyArrayObject *result;
	int i, j;

	static char *kwlist[] = {"m", "n", "a", NULL};

	if(!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|f", kwlist, &m, &n, &a))
		return NULL;

	if(!(result = NA_NewArray(NULL, tFloat32, 2, m, n)))
		return NULL;

	b = 1 - a;

	for(i = 0; i < m; i++) {
		for(j = 0; j < n; j++) {
			((float *)result->data)[i*n + j] = 
				(float)(a - b*cos(2.0*M_PI*((float)i)/((float)(m - 1))))
								*(a - b*cos(2.0*M_PI*((float)j)/((float)(n - 1))));
		}
	}

	return NA_OutputArray(result, tFloat32, 0);
}

static PyObject *highpass(PyObject *self, PyObject *args) {
	int m, n;
	PyArrayObject *result;
	int i, j;
	float x;

	if(!PyArg_ParseTuple(args, "ii", &m, &n))
		return NULL;

	if(!(result = NA_NewArray(NULL, tFloat32, 2, m, n)))
		return NULL;

	for(i = 0; i < m; i++) {
		for(j = 0; j < n; j++) {
			x = cos(M_PI*((((float)i)/((float)m)) - 0.5))
						*cos(M_PI*((((float)j)/(2.0*((float)n)))));
			((float *)result->data)[i*n + j] = (float)((1.0 - x)*(2.0 - x));
		}
	}

	return NA_OutputArray(result, tFloat32, 0);
}

float bilinear(float *array, int m, int n, float x, float y) {
	int x0, y0, x1, y1;
	float v00 = 0.0, v01 = 0.0, v10 = 0.0, v11 = 0.0;
	x0 = (int)x;
	y0 = (int)y;
	x1 = x0 + 1;
	y1 = y0 + 1;
	if((x0 < n) && (y0 < m) && (x0 >= 0) && (y0 >= 0))
		v00 = array[y0*n + x0];
	if((x1 < n) && (y0 < m) && (x1 >= 0) && (y0 >= 0))
		v01 = array[y0*n + x1];
	if((x0 < n) && (y1 < m) && (x0 >= 0) && (y1 >= 0))
		v10 = array[y1*n + x0];
	if((x1 < n) && (y1 < m) && (x1 >= 0) && (y1 >= 0))
		v01 = array[y1*n + x1];
	return (v00*(y1 - y)*(x1 - x)) + (v01*(y1 - y)*(x - x0))
					+ (v10*(y - y0)*(x1 - x)) + (v11*(y - y0)*(x - x0));
}

float nearestneighbor(float *array, int m, int n, float x, float y) {
	int x0 = (int)(x + 0.5);
	int y0 = (int)(y + 0.5);
	if((x0 < 0) || (y0 < 0) || (x0 >= n) || (y0 >= m))
		return 0.0;
	return array[y0*n + x0];
}

static PyObject *logpolar(PyObject *self, PyObject *args) {
	PyObject *input;
	int phis, logrhos;
	double center[2];
	double maxr;
	double mintheta, maxtheta;
	double base, phiscale;
	PyArrayObject *iarray, *oarray;
	int i, j, logrho, phi;
	double r, logr, theta, x, y;
	float *a, *c;
	int size, index;

	if(!PyArg_ParseTuple(args, "Oiiddddd", &input, &phis, &logrhos,
																	&(center[0]), &(center[1]),
																	&maxr, &mintheta, &maxtheta))
		return NULL;

	iarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY);

	/*
	center[0] = (double)iarray->dimensions[0]/2.0;
	center[1] = (double)iarray->dimensions[1]/2.0;
	
	if(iarray->dimensions[0]/2 < iarray->dimensions[1])
		maxr = (double)iarray->dimensions[0]/2.0;
	else
		maxr = (double)iarray->dimensions[1]/2.0;
	*/

	base = pow(maxr + 1.0, 1.0/logrhos);

	phiscale = (double)phis/(maxtheta - mintheta);

	a = (float *)malloc(logrhos*phis*sizeof(float));
	c = (float *)malloc(logrhos*phis*sizeof(float));
	memset((void *)a, 0, logrhos*phis*sizeof(float));
	memset((void *)c, 0, logrhos*phis*sizeof(float));

	size = logrhos*phis;
	for(i = 0; i < iarray->dimensions[0]; i++) {
		for(j = 0; j < iarray->dimensions[1]; j++) {
			x = j + 0.5 - center[1];
			y = i + 0.5 - center[0];
			logr = log(sqrt(x*x + y*y) + 1.0)/log(base);
			theta = atan2(y, x);
			logrho = (int)(logr + 0.5);
			phi = (int)((theta - mintheta)*phiscale + 0.5);
			index = logrho*phis + phi;
			if((index >= 0) && (index < size)) {
				a[index] += ((float *)iarray->data)[i*iarray->dimensions[1] + j];
				c[index] += 1;
			}
		}
	}

	if(!(oarray = NA_NewArray(NULL, tFloat32, 2, logrhos, phis)))
		return NULL;

	for(logrho = 0; logrho < logrhos; logrho++) {
		for(phi = 0; phi < phis; phi++) {
			if(c[logrho*phis + phi] > 0) {
				((float *)oarray->data)[logrho*oarray->dimensions[1] + phi] =
															a[logrho*phis + phi]/(float)c[logrho*phis + phi];
			} else {
				logr = (double)logrho + 0.5;
				r = pow(base, logr - 1.0);
				theta = ((double)phi + 0.5)/phiscale + mintheta;
				x = r*cos(theta);
				y = r*sin(theta);
				i = (int)(y - 0.5 + center[0] + 0.5);
				j = (int)(x - 0.5 + center[1] + 0.5);
				if((i >= 0) && (i < iarray->dimensions[0])
						&& (j >= 0) && (j < iarray->dimensions[1])) {
					((float *)oarray->data)[logrho*oarray->dimensions[1] + phi] =
													((float *)iarray->data)[i*iarray->dimensions[1] + j];
				}
			}
		}
	}

	free(c);
	free(a);

	Py_XDECREF(iarray);

	return Py_BuildValue("(Off)", NA_OutputArray(oarray, tFloat32, 0), base, phiscale);
}

static struct PyMethodDef numeric_methods[] = {
	{"min", min, METH_VARARGS},
	{"max", max, METH_VARARGS},
	{"minmax", minmax, METH_VARARGS},
	{"stdev", stdev, METH_VARARGS},
	{"blobs", blobs, METH_VARARGS},
	{"despike", despike, METH_VARARGS},
	{"bin", bin, METH_VARARGS},
	{"nonmaximasuppress", nonmaximasuppress, METH_VARARGS},
	{"hysteresisthreshold", hysteresisthreshold, METH_VARARGS},
	{"houghline", houghline, METH_VARARGS},
	{"linearscale", linearscale, METH_VARARGS},
	{"rgbstring", rgbstring, METH_VARARGS},
	{"hanning", hanning, METH_VARARGS|METH_KEYWORDS},
	{"highpass", highpass, METH_VARARGS},
	{"logpolar", logpolar, METH_VARARGS},
	{NULL, NULL}
};

void initnumextension()
{
	(void) Py_InitModule("numextension", numeric_methods);
	import_libnumarray()
}

