#include <Python.h>
#include <numpy/arrayobject.h>
#include <math.h>
#include <complex.h>
#include "imgbase.h"
#include "edge.h"
#include <fftw.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifndef M_PI_2
#define M_PI_2 1.57079632679489661923
#endif

#ifndef M_SQRT2
#define M_SQRT2 1.41421356237309504880
#endif

#undef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#undef MAX
#define MAX(a,b) ((a) > (b) ? (a) : (b))


/******************************************
 statistical functions
******************************************/

static PyObject * radialPower( PyObject * self, PyObject * args );

/****
The minmax function calculates both min and max of an array in one loop.
It is faster than the sum of both min and max above because it does
3 comparisons for every 2 elements, rather than two comparison for every 
element
****/

static PyObject * minmax(PyObject *self, PyObject *args) {
	PyObject *input, *inputarray;
	PyArray_Descr *inputdesc;
	float *iter;
	float minresult, maxresult;
	int i;
	unsigned long len;

	if (!PyArg_ParseTuple(args, "O", &input))
		return NULL;

	/* create proper PyArrayObjects from input source */
	inputdesc = PyArray_DescrNewFromType(NPY_FLOAT32);
	inputarray = PyArray_FromAny(input, inputdesc, 0, 0, NPY_CARRAY|NPY_FORCECAST, NULL);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	len = PyArray_SIZE(inputarray);

	iter = (float *)PyArray_DATA(inputarray);
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
	
	PyObject *input_image, *output_image;
	float sigma = 1.0;
	
	if ( !PyArg_ParseTuple(args, "Of", &input_image, &sigma) ) return NULL;
	
	int krad = sigma * 4;
	krad = MAX(krad,2);

	float *kernel = malloc(sizeof(float)*krad);
	float two_s2  = 1.0 / ( sigma * sigma * 2 );
	float norm    = 1.0 / ( sigma * sqrt( 2 * M_PI ) );
	
	int d, k, i, r;
	
	for (i=0;i<krad;i++) kernel[i] = norm * exp( -i*i*two_s2 );
	
	int   ndim = PyArray_NDIM(input_image);
	npy_intp *dims = PyArray_DIMS(input_image);
	int   size = PyArray_SIZE(input_image);
	
	output_image = PyArray_SimpleNew(ndim, dims, NPY_FLOAT32);
	
	fprintf(stderr,"Blurring matrix with %d dimensions :",ndim);
	for(d=0;d<ndim;d++) fprintf(stderr,"%d.",(int)dims[d]);
	fprintf(stderr," with sigma %f\n",sigma);

	float * tmp_pixels = malloc(sizeof(float)*size);
	float * inp_pixels = (float *)PyArray_DATA(input_image);
	float * out_pixels = (float *)PyArray_DATA(output_image);
	
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
	
	return output_image; 

} 

static PyObject * despike(PyObject *self, PyObject *args) {
	PyObject *image, *floatimage;
	int rows, cols, size, debug;
	float ztest;
	int spikes;
	float ppm;
	PyArray_Descr *desc;

	if (!PyArg_ParseTuple(args, "Oifi", &image, &size, &ztest, &debug))
		return NULL;

	/* must be 2-d array */
	if (PyArray_NDIM(image) != 2) {
		PyErr_SetString(PyExc_ValueError, "image array must be two-dimensional");
		return NULL;
	}

	/* create an array object copy of input data */
	desc = PyArray_DescrNewFromType(NPY_FLOAT32);
	floatimage = PyArray_FromAny(image, desc, 0, 0, NPY_UPDATEIFCOPY | NPY_FORCECAST | NPY_CARRAY, NULL);
	if (floatimage == NULL) {
		Py_XDECREF(floatimage);
		return NULL;
	}

	rows = PyArray_DIMS(floatimage)[0];
	cols = PyArray_DIMS(floatimage)[1];

	spikes = despike_FLOAT((float *)PyArray_DATA(floatimage), rows, cols, size, ztest);
	ppm = 1000000.0 * spikes / (rows * cols);
	if(debug) printf("spikes: %d, ppm: %.1f\n", spikes, ppm);

	Py_XDECREF(floatimage);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * bin(PyObject *self, PyObject *args) {
	PyObject *image, *floatimage, *result;
	int binsize, rows, cols;
	npy_intp newdims[2];
	float *original, *resultrow, *resultpixel;
	int i, j, ib, jb;
	int resrows, rescols, n;
	char errstr[80];
	unsigned long reslen;
	PyArray_Descr *desc;

	if (!PyArg_ParseTuple(args, "Oi", &image, &binsize))
		return NULL;

	/* must be 2-d array */
	if (PyArray_NDIM(image) != 2) {
		PyErr_SetString(PyExc_ValueError, "image array must be two-dimensional");
		return NULL;
	}

	/* must be able to be binned by requested amount */
	rows = PyArray_DIMS(image)[0];
	cols = PyArray_DIMS(image)[1];
	if ((rows%binsize) || (cols%binsize) ) {
		sprintf(errstr, "image dimensions %d,%d do not allow binning by %d", rows,cols,binsize);
		PyErr_SetString(PyExc_ValueError, errstr);
		return NULL;
	}

	/* create a contiguous float image from input image */
	desc = PyArray_DescrNewFromType(NPY_FLOAT32);
	floatimage = PyArray_FromAny(image, desc, 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);
	if (floatimage == NULL) return NULL;


	/* create a float image for result */
	resrows = rows / binsize;
	rescols = cols / binsize;
	newdims[0] = resrows;
	newdims[1] = rescols;
	result = PyArray_SimpleNew(2, newdims, NPY_FLOAT32);
	reslen = PyArray_SIZE(result);

	/* zero the result */
	resultpixel = (float *)PyArray_DATA(result);
	for(i=0; i<reslen; i++) {
		*resultpixel = 0.0;
		resultpixel++;
	}

	/* calc sum of the bins */
	resultpixel = resultrow = (float *)PyArray_DATA(result);
	original = (float *)PyArray_DATA(floatimage);
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
	resultpixel = (float *)PyArray_DATA(result);
	n = binsize * binsize;
	for(i=0; i<reslen; i++) {
		*resultpixel /= n;
		resultpixel++;
	}

	Py_DECREF(floatimage);

	return result;
}

static PyObject * nonmaximasuppress(PyObject *self, PyObject *args) {
	PyObject *input, *gradient;
	PyObject *inputarray, *gradientarray;
	int window = 7;
	int i, j, k;
	double m, theta, sintheta, costheta;
	PyArray_Descr *desc;

	if(!PyArg_ParseTuple(args, "OO|i", &input, &gradient, &window))
		return NULL;

	desc = PyArray_DescrNewFromType(NPY_FLOAT64);
	inputarray = PyArray_FromAny(input, desc, 0, 0, NPY_UPDATEIFCOPY | NPY_FORCECAST | NPY_CARRAY, NULL);
	desc = PyArray_DescrNewFromType(NPY_FLOAT64);
	gradientarray = PyArray_FromAny(gradient, desc, 0, 0, NPY_UPDATEIFCOPY | NPY_FORCECAST | NPY_CARRAY, NULL);

	for(i = 0; i < PyArray_NDIM(inputarray); i++)
		if(PyArray_DIMS(inputarray)[i] != PyArray_DIMS(gradientarray)[i])
			return NULL;

	for(i = window/2; i < PyArray_DIMS(inputarray)[0] - window/2; i++) {
		for(j = window/2; j < PyArray_DIMS(inputarray)[1] - window/2; j++) {
			m = *(double *)(PyArray_DATA(inputarray) + i*PyArray_STRIDES(inputarray)[0]
																				+ j*PyArray_STRIDES(inputarray)[1]);
			theta = *(double *)(PyArray_DATA(gradientarray) + i*PyArray_STRIDES(gradientarray)[0]
																							+ j*PyArray_STRIDES(gradientarray)[1]);
			sintheta = sin(theta);
			costheta = cos(theta);
			for(k = -window/2; k <= window/2; k++) {
				if(m < *(double *)(PyArray_DATA(inputarray)
													+ (i + (int)(k*sintheta + 0.5))*PyArray_STRIDES(inputarray)[0]
													+ (j + (int)(k*costheta + 0.5))*PyArray_STRIDES(inputarray)[1]))
					*(double *)(PyArray_DATA(inputarray) + i*PyArray_STRIDES(inputarray)[0]
																				+ j*PyArray_STRIDES(inputarray)[1]) = 0.0;
			}
		}
	}
	Py_DECREF(inputarray);
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * hysteresisthreshold(PyObject *self, PyObject *args) {
	PyObject *input;
	PyObject *inputarray, *outputarray;
	int i, j, k, l;
	float lowthreshold, highthreshold;
	PyArray_Descr *desc;

	if(!PyArg_ParseTuple(args, "Off", &input, &lowthreshold, &highthreshold))
		return NULL;

	desc = PyArray_DescrNewFromType(NPY_FLOAT64);
	inputarray = PyArray_FromAny(input, desc, 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);
	outputarray = PyArray_SimpleNew(2, PyArray_DIMS(inputarray), NPY_FLOAT32);

	for(i = 1; i < PyArray_DIMS(inputarray)[0] - 1; i++) {
		for(j = 1; j < PyArray_DIMS(inputarray)[1] - 1; j++) {
			if(*(double *)(PyArray_DATA(inputarray) + i*PyArray_STRIDES(inputarray)[0]
											+ j*PyArray_STRIDES(inputarray)[1]) >= highthreshold) {
				*(int *)(PyArray_DATA(outputarray) + i*PyArray_STRIDES(outputarray)[0]
																		+ j*PyArray_STRIDES(outputarray)[1]) = 1;
				for(k = -1; k <= 1; k++) {
					for(l = -1; l <= 1; l++) {
						if(k == 0 && l == 0)
							continue;
						if(*(double *)(PyArray_DATA(inputarray)
													+ (i + k)*PyArray_STRIDES(inputarray)[0]
													+ (j + l)*PyArray_STRIDES(inputarray)[1]) >= lowthreshold) {
							*(int *)(PyArray_DATA(outputarray) + (i + k)*PyArray_STRIDES(outputarray)[0]
																				+ (j + l)*PyArray_STRIDES(outputarray)[1]) = 1;
						}
					}
				}
			}
		}
	}
	Py_DECREF(inputarray);
	return outputarray;
}

static PyObject * houghline(PyObject *self, PyObject *args) {
	PyObject *input, *gradient = NULL;
	PyObject *inputarray, *gradientarray = NULL, *hough;
	npy_intp dimensions[3];
	int n, i, j, k, kmin, kmax, r, direction=0;
	double rtheta;
	double gradientvalue;
	int ntheta = 90;
	float gradient_tolerance = M_PI/180.0, rscale = 1.0;
	PyArray_Descr *desc;

	if(!PyArg_ParseTuple(args, "O|Ofif", &input, &gradient, &gradient_tolerance,
																				&ntheta, &rscale))
		return NULL;

	desc = PyArray_DescrNewFromType(NPY_FLOAT64);
	inputarray = PyArray_FromAny(input, desc, 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);
	if(gradient != NULL)
		desc = PyArray_DescrNewFromType(NPY_FLOAT64);
		gradientarray = PyArray_FromAny(gradient, desc, 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);

	if(PyArray_DIMS(inputarray)[0] != PyArray_DIMS(inputarray)[1])
		return NULL;

	n = PyArray_DIMS(inputarray)[0];

	dimensions[0] = (int)ceil(M_SQRT2*n) * rscale;
	dimensions[1] = ntheta;
	dimensions[2] = 2;
	hough = PyArray_SimpleNew(3, dimensions, NPY_FLOAT64);

	for(i = 0; i < PyArray_DIMS(inputarray)[0]; i++)
		for(j = 0; j < PyArray_DIMS(inputarray)[1]; j++)
			if(((double *)PyArray_DATA(inputarray))[j * (i + 1)] > 0.0) {
				if(gradientarray != NULL) {
					gradientvalue = *(double *)(PyArray_DATA(gradientarray)
																			+ i*PyArray_STRIDES(gradientarray)[0]
																			+ j*PyArray_STRIDES(gradientarray)[1]);
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
					*(double *)(PyArray_DATA(hough) + r*PyArray_STRIDES(hough)[0]
											+ k*PyArray_STRIDES(hough)[1]
											+ direction*PyArray_STRIDES(hough)[2]) +=
									*(double *)(PyArray_DATA(inputarray) + i*PyArray_STRIDES(inputarray)[0]
															+ j*PyArray_STRIDES(inputarray)[1]);
				}
			}
	Py_DECREF(inputarray);
	Py_DECREF(gradientarray);

	return (PyObject *)hough;
}

static PyObject * rgbstring(PyObject *self, PyObject *args) {
	PyObject *input, *output, *colormap = NULL, *values = NULL, *cvalue = NULL;
	PyObject *inputarray;
	int i, j, size;
	float frommin, frommax, fromrange, scale, value;
	unsigned char *index;
	int scaledvalue;
	float colors = 255.0;
	unsigned char *rgb = NULL;
	PyArray_Descr *desc;

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

	desc = PyArray_DescrNewFromType(NPY_FLOAT32);
	inputarray = PyArray_FromAny(input, desc, 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);

	fromrange = frommax - frommin;
	if(fromrange == 0.0)
		scale = 0.0;
	else
		scale = (float)colors/fromrange;

	size = PyArray_DIMS(inputarray)[0]*PyArray_DIMS(inputarray)[1]*3;
	output = PyString_FromStringAndSize(NULL, size);
	index = (unsigned char *)PyString_AsString(output);
	for(i = 0; i < PyArray_DIMS(inputarray)[0]; i++) {
		for(j = 0; j < PyArray_DIMS(inputarray)[1]; j++) {
			value = *(float *)(PyArray_DATA(inputarray)
												+ i*PyArray_STRIDES(inputarray)[0] + j*PyArray_STRIDES(inputarray)[1]);
			
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

static PyObject * hanning(PyObject * self, PyObject *args, PyObject *kwargs) {
	int m, n;
	npy_intp dims[2];
	float a = 0.5, b;
	PyObject *result;
	int i, j;

	static char *kwlist[] = {"m", "n", "a", NULL};

	if(!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|f", kwlist, &m, &n, &a))
		return NULL;

	dims[0] = m;
	dims[1] = n;

	result = PyArray_SimpleNew(2, dims, NPY_FLOAT32);
	if(!result)
		return NULL;

	b = 1 - a;

	for(i = 0; i < m; i++) {
		for(j = 0; j < n; j++) {
			((float *)PyArray_DATA(result))[i*n + j] = 
				(float)(a - b*cos(2.0*M_PI*((float)i)/((float)(m - 1))))
								*(a - b*cos(2.0*M_PI*((float)j)/((float)(n - 1))));
		}
	}

	return result;
}

static PyObject * highpass(PyObject *self, PyObject *args) {
	int m, n;
	PyObject *result;
	int i, j;
	float x;
	npy_intp dims[2];

	if(!PyArg_ParseTuple(args, "ii", &m, &n))
		return NULL;

	dims[0] = m;
	dims[1] = n;
	result = PyArray_SimpleNew(2, dims, NPY_FLOAT32);
	if(!result)
		return NULL;

	for(i = 0; i < m; i++) {
		for(j = 0; j < n; j++) {
			x = cos(M_PI*((((float)i)/((float)m)) - 0.5))
						*cos(M_PI*((((float)j)/(2.0*((float)n)))));
			((float *)PyArray_DATA(result))[i*n + j] = (float)((1.0 - x)*(2.0 - x));
		}
	}

	return result;
}

static PyObject * radialPower( PyObject * self, PyObject * args ) {
	
	// Caveats to this function:
	//  1.  The inverting used to center the FFT in the middle is only technically accurate when the
	//      image dimensions are multiples of 2
	//  2.  TODO: The function could be made about 2X faster if the R2C fft is used rather than the complex fft
	//  3.  The radial averaging should be done based on the sampling frequency along both axis, right now the
	//      averaging is not correct if the image dimensions are not the same.
	
	fprintf(stderr,"Computing power spectrum...");
	
	int i, k;
	float sigma = 0;
	PyObject * image;
	PyArray_Descr * type;
	
	if ( !PyArg_ParseTuple(args,"Of",&image,&sigma) ) return NULL;
	
	type = PyArray_DescrNewFromType(NPY_FLOAT64);
	image = PyArray_FromAny(image,type,0,0,NPY_CARRAY|NPY_FORCECAST,NULL);

	npy_intp * dims = PyArray_DIMS(image);	
	npy_intp ndim = PyArray_NDIM(image);
	npy_intp size = PyArray_SIZE(image);
	
	if ( ndim != 2 ) return NULL;
	
	int cur_pos[ndim+1];
	int cur_dim[ndim+1];
	
	for(i=0;i<ndim+1;i++) cur_pos[i] = 0;
	for(i=0;i<ndim;i++) cur_dim[i] = dims[i];
	cur_dim[ndim] = 0;
	
	double * data = PyArray_DATA(image);
	complex * fft = fftw_malloc(sizeof(complex)*size);
	
	int flip_state = 0;
	for(i=0;i<size;i++) {
			
		for(k=0;cur_pos[k]==cur_dim[k];k++) {
			cur_pos[k] = 0;
			cur_pos[k+1]++;
			flip_state = flip_state - cur_dim[k] + 1;
		}
		
		if ( flip_state % 2 == 0 ) fft[i] = (fftw_complex)(data[i]);
		else fft[i] = -(fftw_complex)(data[i]);

		cur_pos[0]++; flip_state++;
		
	}
	
	fftw_plan plan = fftw_plan_dft(ndim, cur_dim, fft, fft, FFTW_FORWARD, FFTW_ESTIMATE);
	fftw_execute(plan);
	
	for (i=0;i<size;i++) {
		double real = creal(fft[i]);
		double imag = cimag(fft[i]);
		data[i] = real*real + imag*imag;
	}
	
	fftw_destroy_plan(plan);
	free(fft);
	
	fprintf(stderr,"DONE\n");
	
	fprintf(stderr,"Computing radial average...");
	
	// Now we rotationally average the power spectrum
	
	int rows = cur_dim[0];
	int cols = cur_dim[1];
	int rad_size = MIN(rows/2,cols/2);
	
	double x_rad = cols / 2.0;
	double y_rad = rows / 2.0;

	npy_intp rad_dim[1] = { rad_size };
	PyObject * radial_avg = PyArray_SimpleNew(1,rad_dim,NPY_FLOAT64);
	if (radial_avg == NULL) return NULL;
	
	double * rad_avg = PyArray_DATA(radial_avg); 
	double * rad_cnt = malloc(sizeof(double)*rad_size);
	if (rad_avg == NULL) return NULL;
	if (rad_cnt == NULL) return NULL;
	
	for(i=0;i<rad_size;i++) rad_avg[i] = 0.0;
	for(i=0;i<rad_size;i++) rad_cnt[i] = 0.0;
	
	int r,c;
	for(r=0;r<rows;r++) {
		for(c=0;c<cols;c++) {
			double x = c - x_rad;
			double y = r - y_rad;
			double rad = sqrt(x*x+y*y);
			if ( rad >= rad_size-1 ) continue;
			if ( rad < 5 ) continue;
			int i_rad = rad;
			double rwt1 = rad - i_rad;
			double rwt2 = 1.0 - rwt1;
			rad_avg[i_rad] += rwt2 * data[r*cols+c];
			rad_avg[i_rad+1] += rwt1 * data[r*cols+c];
			rad_cnt[i_rad] += rwt2;
			rad_cnt[i_rad+1] += rwt1;
		}
	}
	
	for(i=0;i<rad_size;i++) if ( rad_cnt[i] != 0.0 ) rad_avg[i] = rad_avg[i] / rad_cnt[i];
	for(i=0;i<rad_size;i++) rad_avg[i] = sqrt(rad_avg[i]);	
	
//	for(i=0,k=0;i<rad_size-1;i++,k+=2) rad_avg[i] = rad_avg[k] + rad_avg[k+1];
//	for(i=0,k=0;i<rad_size-1;i++,k+=2) rad_avg[i] = rad_avg[k] + rad_avg[k+1];
	
//	for(i=0;i<rad_size/4;i++) fprintf(stderr,"%e\n",rad_avg[i]);
	
	free(rad_cnt);
	
	fprintf(stderr,"DONE\n");
	
	if ( sigma == 0.0 ) return radial_avg;
	
	fprintf(stderr,"Performing background normalization with sigma %2.2f...",sigma);
	
	int krad = sigma * 4;
	krad = MAX(krad,1);
	double * kernel = malloc(sizeof(double)*krad);
	double * low_pass = malloc(sizeof(double)*rad_size);
	
	if ( kernel == NULL || low_pass == NULL ) { free(low_pass); free(kernel); return radial_avg; }

	double two_s2  = 1.0 / ( sigma * sigma * 2.0 );
	double norm    = 1.0 / ( sigma * sqrt(2.0*M_PI) );
	
	for (i=0;i<krad;i++) kernel[i] = norm * exp( -(double)i*(double)i*two_s2 );

	for(i=0;i<rad_size;i++) {
		double sum = rad_avg[i] * kernel[0];
		for(k=1;k<krad;k++) {
			int pos1 = i - k;
			int pos2 = i + k;
			if ( pos1 < 0 ) pos1 = 0;
			if ( pos2 > rad_size-1 ) pos2 = rad_size-1;
			sum += ( rad_avg[pos1] + rad_avg[pos2] ) * kernel[k];
		}
		low_pass[i] = sum;
	}
	
	for(i=0;i<rad_size;i++) rad_avg[i] = rad_avg[i] / low_pass[i];
	free(kernel);
	free(low_pass);

	fprintf(stderr,"DONE\n");
	
	return radial_avg;
	
}

static PyObject * logpolar(PyObject *self, PyObject *args) {
	PyObject *input;
	int phis, logrhos;
	double center[2];
	double maxr;
	double mintheta, maxtheta;
	double base, phiscale;
	PyObject *iarray, *oarray;
	int i, j, logrho, phi;
	double r, logr, theta, x, y;
	float *a, *c;
	int size, index;
	PyArray_Descr *desc;
	npy_intp dims[2];

	if(!PyArg_ParseTuple(args, "Oiiddddd", &input, &phis, &logrhos,
																	&(center[0]), &(center[1]),
																	&maxr, &mintheta, &maxtheta))
		return NULL;

	desc = PyArray_DescrNewFromType(NPY_FLOAT32);
	iarray = PyArray_FromAny(input, desc, 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);

	/*
	center[0] = (double)PyArray_DIMS(iarray)[0]/2.0;
	center[1] = (double)PyArray_DIMS(iarray)[1]/2.0;
	
	if(PyArray_DIMS(iarray)[0]/2 < PyArray_DIMS(iarray)[1])
		maxr = (double)PyArray_DIMS(iarray)[0]/2.0;
	else
		maxr = (double)PyArray_DIMS(iarray)[1]/2.0;
	*/

	base = pow(maxr + 1.0, 1.0/logrhos);

	phiscale = (double)phis/(maxtheta - mintheta);

	a = (float *)malloc(logrhos*phis*sizeof(float));
	c = (float *)malloc(logrhos*phis*sizeof(float));
	memset((void *)a, 0, logrhos*phis*sizeof(float));
	memset((void *)c, 0, logrhos*phis*sizeof(float));

	size = logrhos*phis;
	for(i = 0; i < PyArray_DIMS(iarray)[0]; i++) {
		for(j = 0; j < PyArray_DIMS(iarray)[1]; j++) {
			x = j + 0.5 - center[1];
			y = i + 0.5 - center[0];
			logr = log(sqrt(x*x + y*y) + 1.0)/log(base);
			theta = atan2(y, x);
			logrho = (int)(logr + 0.5);
			phi = (int)((theta - mintheta)*phiscale + 0.5);
			index = logrho*phis + phi;
			if((index >= 0) && (index < size)) {
				a[index] += ((float *)PyArray_DATA(iarray))[i*PyArray_DIMS(iarray)[1] + j];
				c[index] += 1;
			}
		}
	}

	dims[0] = logrhos;
	dims[1] = phis;
	oarray = PyArray_SimpleNew(2, dims, NPY_FLOAT32);
	if(!oarray)
		return NULL;

	for(logrho = 0; logrho < logrhos; logrho++) {
		for(phi = 0; phi < phis; phi++) {
			if(c[logrho*phis + phi] > 0) {
				((float *)PyArray_DATA(oarray))[logrho*PyArray_DIMS(oarray)[1] + phi] =
															a[logrho*phis + phi]/(float)c[logrho*phis + phi];
			} else {
				logr = (double)logrho + 0.5;
				r = pow(base, logr - 1.0);
				theta = ((double)phi + 0.5)/phiscale + mintheta;
				x = r*cos(theta);
				y = r*sin(theta);
				i = (int)(y - 0.5 + center[0] + 0.5);
				j = (int)(x - 0.5 + center[1] + 0.5);
				if((i >= 0) && (i < PyArray_DIMS(iarray)[0])
						&& (j >= 0) && (j < PyArray_DIMS(iarray)[1])) {
					((float *)PyArray_DATA(oarray))[logrho*PyArray_DIMS(oarray)[1] + phi] =
													((float *)PyArray_DATA(iarray))[i*PyArray_DIMS(iarray)[1] + j];
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
int isLocalMaximum(double *buffer, int filter_size, double *return_value, void *callback_data) {
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
int isLocalMinimum(double *buffer, int filter_size, double *return_value, void *callback_data) {
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

static PyObject * py_isLocalMaximum(PyObject *obj, PyObject *args) {
	int center_index;
	if (!PyArg_ParseTuple(args, "i", &center_index)) {
		PyErr_SetString(PyExc_RuntimeError, "invalid parameters");
		return NULL;
	} else {
		/* wrap function and callback_data in a CObject: */
		return PyCObject_FromVoidPtrAndDesc(isLocalMaximum, &center_index, NULL);
	}
}

static PyObject * py_isLocalMinimum(PyObject *obj, PyObject *args) {
	int center_index;
	if (!PyArg_ParseTuple(args, "i", &center_index)) {
		PyErr_SetString(PyExc_RuntimeError, "invalid parameters");
		return NULL;
	} else {
		/* wrap function and callback_data in a CObject: */
		return PyCObject_FromVoidPtrAndDesc(isLocalMinimum, &center_index, NULL);
	}
}

int pointInPolygon(float x, float y, float *polygon, int nvertices) {
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

static PyObject * py_pointsInPolygon(PyObject *obj, PyObject *args) {
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

void float_to_ubyte( float* image, int nsize, unsigned char* outimg, int scale_flag) {

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

static PyObject *cannyedge(PyObject *self, PyObject *args) {
	PyObject *input;
	PyObject *inputarray=NULL, *outputarraym=NULL, *outputarray=NULL;
	int i;
	unsigned nelements;
	float sigma, tlow, thigh;
	unsigned char *image=NULL;
	short int *magnitude=NULL;
	unsigned char *edge=NULL;

	if(!PyArg_ParseTuple(args, "Offf", &input, &sigma, &tlow, &thigh))
           return NULL;

	inputarray = PyArray_FromAny(input, PyArray_DescrNewFromType(NPY_FLOAT32), 0, 0, NPY_CARRAY | NPY_FORCECAST, NULL);
        if (inputarray == NULL || PyArray_NDIM(inputarray) != 2) {
           PyErr_SetString(PyExc_ValueError, "failed to accept a 2-D array of type FLOAT.\n");
           return NULL;
        }
        
        nelements =  1;
        for (i=0; i< PyArray_NDIM(inputarray); i++)
            nelements *= PyArray_DIMS(inputarray)[i];
        image = (unsigned char *)malloc(nelements);
        if (image == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to allocate a array of unsigned char.\n");
           return NULL;
        }

        float_to_ubyte((float *)PyArray_DATA(inputarray), nelements, image, DO_SCALE);
        canny(image, PyArray_DIMS(inputarray)[0], PyArray_DIMS(inputarray)[1], sigma, tlow, thigh, &magnitude, &edge, NULL);
        if (edge == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to generate canny edge of unsigned char.\n");
           return NULL;
        }
        if (image !=NULL) free(image);
	outputarraym = PyArray_SimpleNewFromData(PyArray_NDIM(inputarray), PyArray_DIMS(inputarray), NPY_INT16, magnitude);
	outputarray = PyArray_SimpleNewFromData(PyArray_NDIM(inputarray), PyArray_DIMS(inputarray), NPY_UINT8, edge);
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

	{"radialPower",radialPower,METH_VARARGS},

	{"cannyedge", cannyedge, METH_VARARGS},

// from beamfinder.c
//	{"resamplearray", resamplearray, METH_VARARGS},
//	{"componentlabeling", componentlabeling, METH_VARARGS}, 
//	{"fitcircle2edges", fitcircle2edges, METH_VARARGS}, 

	{NULL, NULL}
	
};

void initnumextension() {
	Py_InitModule("numextension", numeric_methods);
	import_array();
}

