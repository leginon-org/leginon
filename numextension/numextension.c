#include <Python.h>
#include <numarray/libnumarray.h>
#include <math.h>
#include "imgbase.h"
#include "edge.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef M_PI_2
#define M_PI_2 1.57079632679489661923
#endif

#ifndef M_SQRT2
#define M_SQRT2 1.41421356237309504880
#endif


/******************************************
 statistical functions
******************************************/

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
	int i;
	unsigned long len;

	if (!PyArg_ParseTuple(args, "O", &input))
		return NULL;

	/* create proper PyArrayObjects from input source */
	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	len = NA_elements(inputarray);

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

int despike_FLOAT(float *array, int rows, int cols, int statswidth, float ztest) {
	float *newptr, *oldptr, *rowptr, *colptr;
	int sw2, sw2cols, sw2cols_sw2, sw2cols__sw2;
	int r, c, rr, cc;
	int spikes=0;
	float mean, std, nn;
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

static PyObject * gaussian_nd( PyObject *self, PyObject *args) {
	
	PyArrayObject *input_image, *output_image;
	float sigma = 1.0;
	
	if ( !PyArg_ParseTuple(args, "Of", &input_image, &sigma) ) return NULL;
	
	int krad = sigma * 4;
	krad = MAX(krad,2);
	
	

	float *kernel = malloc(sizeof(float)*krad);
	float two_s2  = 1.0 / ( sigma * sigma * 2 );
	float norm    = 1.0 / ( sigma * sqrt( 2 * M_PI ) );
	
	int d, k, i, r;
	
	for (i=0;i<krad;i++) kernel[i] = norm * exp( -i*i*two_s2 );
	
	int   ndim = input_image->nd;
	int * dims = input_image->dimensions;
	int   size = NA_elements(input_image);
	
	output_image = NA_vNewArray(NULL, tFloat32, ndim, dims);
	
	fprintf(stderr,"Blurring matrix with %d dimensions :",ndim);
	for(d=0;d<ndim;d++) fprintf(stderr,"%d.",dims[d]);
	fprintf(stderr," with sigma %f\n",sigma);

	float * tmp_pixels = malloc(sizeof(float)*size);
	float * inp_pixels = (float *)input_image->data;
	float * out_pixels = (float *)output_image->data;
	
	memcpy(out_pixels,inp_pixels,sizeof(float)*size);

	float *x1 = out_pixels;
	float *x2 = tmp_pixels;
	float *x3 = NULL;

	for(d=0;d<ndim;d++) {
		
		// The number of elements in each 1d vector along dimensions d, and the number of such vectors
		// which is equal to the total number of elements divided by the current dimension length.
		int cols = dims[d];
		int rots = size / dims[d];
		
		// Handy dandy border values (out of range comparisons) used in the MIN, MAX functions below.  
		int minb = 0;
		int maxb = cols - 1;

		int t = 0, x = 0;
		
		// Convolve 1d kernel with 1d vector replicating border pixels.  Write the results along the slowest
		// array dimensions (effectively rotating the array so the next 1d pass will go along the next dimension

		for(k=0;k<size;k+=cols) {
			for(r=0;r<cols;r++) {
				float sum = x1[k+r] * kernel[0];
				for(i=1;i<krad;i++) {
					int pix1 = MAX(minb,r-i) + k;
					int pix2 = MIN(maxb,r+i) + k;
					sum += ( x1[pix1] + x1[pix2] ) * kernel[i];
				}
				x2[t] = sum;
				if ( (t += rots) >= size ) t = ++x;
			}
		}
		
		x3 = x1;
		x1 = x2;
		x2 = x3;
		
	}
	
	if ( x1 != out_pixels ) memcpy(out_pixels,tmp_pixels,size*sizeof(float));
	
	free(kernel);
	free(tmp_pixels);
	
	return (PyObject *)output_image; 

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
	int resrows, rescols, n;
	char errstr[80];
	unsigned long reslen;

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
		sprintf(errstr, "image dimensions %d,%d do not allow binning by %d", rows,cols,binsize);
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
	reslen = NA_elements(result);

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

	return (PyObject *)result;
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
	return (PyObject *)outputarray;
}

static PyObject *houghline(PyObject *self, PyObject *args) {
	PyObject *input, *gradient = NULL;
	PyArrayObject *inputarray, *gradientarray = NULL, *hough;
	int dimensions[3];
	int n, nd;
	int i, j, k, kmin, kmax, r, direction=0;
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

	return (PyObject *)hough;
}

static PyObject *rgbstring(PyObject *self, PyObject *args) {
	PyObject *input, *output, *colormap = NULL, *values = NULL, *cvalue = NULL;
	PyArrayObject *inputarray;
	int i, j, size;
	float frommin, frommax, fromrange, scale, value;
	unsigned char *index;
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

	fromrange = frommax - frommin;
	if(fromrange == 0.0)
		scale = 0.0;
	else
		scale = (float)colors/fromrange;

	size = inputarray->dimensions[0]*inputarray->dimensions[1]*3;
	output = PyString_FromStringAndSize(NULL, size);
	index = (unsigned char *)PyString_AsString(output);
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

	return (PyObject *)result;
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

	return (PyObject *)result;
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

	return Py_BuildValue("(Off)", (PyObject *)oarray, base, phiscale);
}

/*
int FilterFunction(	double *buffer, int filter_size, double *return_value, void *callback_data)
    The calling function iterates over the elements of the input and output arrays, calling the callback function at each element. The elements within the footprint of the filter at the current element are passed through the buffer parameter, and the number of elements within the footprint through filter_size. The calculated valued should be returned in the return_value argument.
*/

/* return 1 if center element of buffer is local maximum, otherwise 0 */
/* callback_data points to index of center element */
int isLocalMaximum(double *buffer, int filter_size, double *return_value, void *callback_data)
{
	double center_value, *p;
	int i;
	center_value = buffer[*(int *)callback_data];
	p = buffer;
	for(i=0; i<filter_size; i++,p++) {
		if(i == *(int *)callback_data) continue;
		if(*p >= center_value) {
			*return_value = 0;
			return 1;
		}
	}
	*return_value = 1;
	return 1;
}

/* return 1 if center element of buffer is local minimum, otherwise 0 */
/* callback_data points to index of center element */
int isLocalMinimum(double *buffer, int filter_size, double *return_value, void *callback_data)
{
	double center_value, *p;
	int i;
	center_value = buffer[*(int *)callback_data];
	p = buffer;
	for(i=0; i<filter_size; i++,p++) {
		if(i == *(int *)callback_data) continue;
		if(*p <= center_value) {
			*return_value = 0;
			return 1;
		}
	}
	*return_value = 1;
	return 1;
}

static PyObject *
py_isLocalMaximum(PyObject *obj, PyObject *args)
{
	int center_index;
	if (!PyArg_ParseTuple(args, "i", &center_index)) {
		PyErr_SetString(PyExc_RuntimeError, "invalid parameters");
		return NULL;
	} else {
		/* wrap function and callback_data in a CObject: */
		return PyCObject_FromVoidPtrAndDesc(isLocalMaximum, &center_index, NULL);
	}
}

static PyObject *
py_isLocalMinimum(PyObject *obj, PyObject *args)
{
	int center_index;
	if (!PyArg_ParseTuple(args, "i", &center_index)) {
		PyErr_SetString(PyExc_RuntimeError, "invalid parameters");
		return NULL;
	} else {
		/* wrap function and callback_data in a CObject: */
		return PyCObject_FromVoidPtrAndDesc(isLocalMinimum, &center_index, NULL);
	}
}


int
pointInPolygon(float x, float y, float *polygon, int nvertices)
{
	int intersections=0;
	float *ax, *ay, *bx, *by;
	int i;

	/* loop through all edges */
	ax = polygon;
	ay = polygon+1;
	bx = polygon+2;
	by = polygon+3;
	for(i=0; i<nvertices-1; i++,ax+=2,ay+=2,bx+=2,by+=2)
	{
		if(*ax == *bx) continue;
		if(
			((*bx < x && *ax >= x) || (*bx >= x && *ax < x)) &&
					(((*by - *ay) / (*bx - *ax) * (x - *ax) + *ay) > y))
		{
			intersections++;
		}
	}

	bx = polygon;
	by = polygon+1;

	if(*ax != *bx)
	{
		if(
			((*bx < x && *ax >= x) || (*bx >= x && *ax < x)) &&
					(((*by - *ay) / (*bx - *ax) * (x - *ax) + *ay) > y))
		{
			intersections++;
		}
	}

	return intersections % 2;
}



static PyObject *
py_pointsInPolygon(PyObject *obj, PyObject *args)
{
	PyObject *points, *polygon, *temp, *temp2, *insidelist, *insidebool;
	float pointx, pointy;
	float *vertices;
	int npoints, nvertices, i, j, k, inside;

	if (!PyArg_ParseTuple(args, "OO", &points, &polygon)) {
		PyErr_SetString(PyExc_RuntimeError, "invalid parameters");
		return NULL;
	}


	/* loop through each vertex, find number of intersections */
	nvertices = PySequence_Size(polygon);
	vertices = (float *)malloc(2*nvertices*sizeof(float));
	for(i=0,k=0; i<nvertices; i++)
	{
		temp = PySequence_GetItem(polygon, i);
		for(j=0; j<2; j++,k++)
		{
			temp2 = PySequence_GetItem(temp, j);
			vertices[k] = PyFloat_AsDouble(temp2);
			Py_DECREF(temp2);
		}
		Py_DECREF(temp);
	}

	npoints = PySequence_Size(points);

	insidelist = PyList_New(npoints);
	for(i=0; i<npoints; i++)
	{
		temp2 = PySequence_GetItem(points, i);
		/* get two float values from point */

		temp = PySequence_GetItem(temp2, 0);
		pointx = PyFloat_AsDouble(temp);
		Py_DECREF(temp);

		temp = PySequence_GetItem(temp2, 1);
		pointy = PyFloat_AsDouble(temp);
		Py_DECREF(temp);

		Py_DECREF(temp2);

		inside = pointInPolygon(pointx, pointy, vertices, nvertices);

		insidebool = PyBool_FromLong(inside);
		PyList_SetItem(insidelist, i, insidebool);
		//Py_DECREF(insidebool);
	}

	free(vertices);

	return insidelist;
}

void float_to_ubyte( float* image, int nsize, unsigned char* outimg, int scale_flag)
{

  int i;
  float min1, max1, scale;

  if(scale_flag == DO_SCALE){
     /* scale the image to 0~255. */
     min1 = image[0];
     max1 = image[0];

     for (i=1; i<nsize; i++)
         if (image[i]<min1)
             min1 = image[i];
         else if (image[i]>max1)
             max1 = image[i];

     if(max1 == min1){
        printf("min == max while scaling float image to UBYTE image.\n");
        return;
      }

      scale = 255.0 / (max1 - min1);
      for (i=0; i<nsize; i++)
           outimg[i]  = (unsigned char)(scale * (image[i] - min1));
  }
  else {
      for(i=0; i<nsize; i++)
         outimg[i]  = (unsigned char)image[i];
  }
}


PyObject *cannyedge(PyObject *self, PyObject *args) {
	PyObject *input;
	PyArrayObject *inputarray=NULL, *outputarraym=NULL, *outputarray=NULL;
	int i, j;
        unsigned pos, nelements;
	float sigma, tlow, thigh;
        unsigned char *image=NULL;
        short int *magnitude=NULL;
        unsigned char *edge=NULL;

	if(!PyArg_ParseTuple(args, "Offf", &input, &sigma, &tlow, &thigh))
           return NULL;

	inputarray = NA_InputArray(input, tFloat32, NUM_C_ARRAY|NUM_COPY);
        if (inputarray == NULL || inputarray->nd != 2) {
           PyErr_SetString(PyExc_ValueError, "failed to accept a 2-D array of type FLOAT.\n");
           return NULL;
        }
        
        nelements =  1;
        for (i=0; i< inputarray->nd; i++)
            nelements *= inputarray->dimensions[i];
        image = (unsigned char *)malloc(nelements);
        if (image == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to allocate a array of unsigned char.\n");
           return NULL;
        }

        float_to_ubyte((float *)inputarray->data, nelements, image, DO_SCALE);
        canny(image, inputarray->dimensions[0], inputarray->dimensions[1], sigma, tlow, thigh, &magnitude, &edge, NULL);
        if (edge == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to generate canny edge of unsigned char.\n");
           return NULL;
        }
/*
	outputarray = (PyArrayObject *)PyArray_FromDims(inputarray->nd, inputarray->dimensions, PyArray_UBYTE);
        pos = 0;
	for (i = 0; i < inputarray->dimensions[0]; i++) 
            for (j = 0; j < inputarray->dimensions[1]; j++, pos++)
		*(unsigned char *)(outputarray->data + i*outputarray->strides[0] + j*outputarray->strides[1]) = edge[pos];
        if (edge !=NULL) free(edge);
*/
        if (image !=NULL) free(image);
	outputarraym = NA_vNewArray(magnitude, tInt16, inputarray->nd, inputarray->dimensions); 
	outputarray = NA_vNewArray(edge, tUInt8, inputarray->nd, inputarray->dimensions); 
	Py_DECREF(inputarray);

	//return (PyObject *)outputarray;
	return Py_BuildValue("OO", outputarray, outputarraym);

}



static struct PyMethodDef numeric_methods[] = {
// used by align, ImageViewer2,
	{"minmax", minmax, METH_VARARGS},

// used by rctacquisition, maybe could use nd_image interpolation instead
	{"bin", bin, METH_VARARGS},

// should find a way to do this using numarray
	{"despike", despike, METH_VARARGS},
	
// craig's fast multi-dimensional gaussian blur
	{"gaussian",gaussian_nd,METH_VARARGS},

// used by Leginon.squarefinder2.py
	{"nonmaximasuppress", nonmaximasuppress, METH_VARARGS},
	{"hysteresisthreshold", hysteresisthreshold, METH_VARARGS},
	{"houghline", houghline, METH_VARARGS},

// used by Leginon.gui.wx.ImageViewer and ImageViewer2
	{"rgbstring", rgbstring, METH_VARARGS},

// used by Leginon.align
	{"hanning", hanning, METH_VARARGS|METH_KEYWORDS},
	{"highpass", highpass, METH_VARARGS},
	{"logpolar", logpolar, METH_VARARGS},

// new stuff
	{"islocalmaximum", py_isLocalMaximum, METH_VARARGS},
	{"islocalminimum", py_isLocalMinimum, METH_VARARGS},
	{"pointsInPolygon", py_pointsInPolygon, METH_VARARGS},

// from beamfinder.c
	//{"resamplearray", resamplearray, METH_VARARGS},
	{"cannyedge", cannyedge, METH_VARARGS}, 
	//{"componentlabeling", componentlabeling, METH_VARARGS}, 
	//{"fitcircle2edges", fitcircle2edges, METH_VARARGS}, 

	{NULL, NULL}
};

void initnumextension()
{
	(void) Py_InitModule("numextension", numeric_methods);
	import_libnumarray()
}

