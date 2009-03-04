#include <Python.h>
#include <numpy/arrayobject.h>
#include "geometry.h"
#include "util.h"
#include "image.h"
#include "mser.h"
#include "csift.h"
#include "match.h"
#include "lautil.h"

Image FMatrixToImage( float *data, int rows, int cols );
static Image PyArrayToImage( PyObject *object );
static PyObject *ImageToPyArray( Image image );
float *GaussianBlurF( float *p1, int rows, int cols, float sigma );
int IsMinPeak( float *p1, int r, int c, float cur );
static PyObject *RegionToPyObject( Region r );
float *SubtractF( float *p1, float *p2, int size );
static Polygon PyArrayToPolygon( PyObject *object );
static PyObject *PolygonToPyArray( Polygon poly );
void BinFMatrix( float *A, int rows, int cols, int bin );

float *GaussianBlurF( float *p1, int rows, int cols, float sigma ) {
	
	int r, c, i;
	int maxc = cols-1;
	int minc = 0;
	
	int krad = sigma*3;
	if ( krad >= rows || krad >= cols ) krad = MIN(rows,cols);
	krad = MAX(krad,1);
	
	float *p2 = malloc(sizeof(float)*rows*cols);
	float *p3 = malloc(sizeof(float)*rows*cols);

	float *kernel = malloc(sizeof(float)*krad);
	float sigma2sq = sigma*sigma*2;
	float max = 0;
	
	for (i=0;i<krad;i++) kernel[i] = exp(-(i*i)/sigma2sq);
	for (i=0;i<krad;i++) max += kernel[i]; max *= 2;
	for (i=0;i<krad;i++) kernel[i] /= max;
	
	for(r=0;r<rows;r++) {
		for(c=0;c<cols;c++) {
			float sum = 0;
			for(i=0;i<krad;i++) {
				int pix1 = MIN(c+i,maxc) + r*cols;
				int pix2 = MAX(c-i,minc) + r*cols;
				sum += ( p1[pix1] + p1[pix2] ) * kernel[i];
			}
			p2[c*rows+r] = sum;
		}
	}
	
	for(r=0;r<rows;r++) {
		for(c=0;c<cols;c++) {
			float sum = 0;
			for(i=0;i<krad;i++) {
				int pix1 = MIN(c+i,maxc) + r*cols;
				int pix2 = MAX(c-i,minc) + r*cols;
				sum += ( p2[pix1] + p2[pix2] ) * kernel[i];
			}
			p3[c*rows+r] = sum;
		}
	}
	
	free(kernel);
	free(p2);
	
	return p3;

}

int IsMinPeak( float *p1, int r, int c, float cur ) {
	
	if ( p1[r+1] >= cur ) return FALSE;
	if ( p1[r-1] >= cur ) return FALSE;
	if ( p1[r+c] >= cur ) return FALSE;
	if ( p1[r-c] >= cur ) return FALSE;
	if ( p1[r+1+c] >= cur ) return FALSE;
	if ( p1[r+1-c] >= cur ) return FALSE;
	if ( p1[r-1+c] >= cur ) return FALSE;
	if ( p1[r-1-c] >= cur ) return FALSE;
	
	return TRUE;
	
}

float *SubtractF( float *p1, float *p2, int size ) {
	int r;
	for(r=0;r<size;r++) p1[r] = p1[r] - p2[r]; 
	return p1;
}

void BinFMatrix( float *A, int rows, int cols, int bin ) {
	
	int k, iterations = log(bin) / log(2);
	
	if ( cols%2 != 0 ) cols--;
	if ( rows%2 != 0 ) rows--;
	
	for(k=0;k<iterations;k++) {
		int r, c, nr = 0, i = 0;
		for(r=0;r<rows;r+=2) {
			for(c=0;c<cols;c+=2) {
				A[i++] = A[nr+c] + A[nr+cols+c] + A[nr+c+1] + A[nr+cols+c+1];
			}
			nr += cols + cols;
		}
		rows /= 2;
		cols /= 2;
	}

}

Image FMatrixToImage( float *data, int rows, int cols ) {
	int r;
	Image im1 = CreateImage(rows,cols);
	for(r=0;r<rows*cols;r++) im1->pixels[0][r] = data[r];
	EnhanceImage(im1,0,255,0.001,0.001);
	return im1;
}

static PyObject *PyMatchImages(PyObject *self, PyObject *args) {

	PyObject *oim1, *oim2;

	float minSize = 0.002, maxSize = 0.9, blur = 0.0, sharpen = 0.0;
	int U = TRUE, D = TRUE;
	if (!PyArg_ParseTuple(args, "OOffffii", &oim1, &oim2, &minSize, &maxSize, &blur, &sharpen, &U, &D )) return NULL;
	
	Image im1 = PyArrayToImage( oim1 );
	Image im2 = PyArrayToImage( oim2 );

	PStack im1keys = NewPStack(100);
	PStack im1desc = NewPStack(100);
	PStack im2keys = NewPStack(100);
	PStack im2desc = NewPStack(100);
	PStack matches = NewPStack(100);
	
	FindMSERegions(im1,im1keys,minSize,maxSize,blur,sharpen,U,D);
	RegionsToSIFTDescriptors(im1keys,im1desc,4,8,41);
	fprintf(stderr,"Image 1: keypoints: %d; descriptors: %d\n",im1keys->stacksize,im1desc->stacksize);
	
	FindMSERegions(im2,im2keys,minSize,maxSize,blur,sharpen,U,D);
	RegionsToSIFTDescriptors(im2keys,im2desc,4,8,41);
	fprintf(stderr,"Image 2: keypoints: %d; descriptors: %d\n",im2keys->stacksize,im2desc->stacksize);

	double **transform = AllocDMatrix(3,3,0,0);
	FindMatches(im1desc,im2desc,matches,20);
	fprintf(stderr,"Found %d matches between images\n",matches->stacksize-1);
	ScreenMatches(matches,transform);
	
	fprintf(stderr,"Freeing all mem\n");
	
	FreeImage(im1);
	FreeImage(im2);
	
	freeRegions(im1keys);
	freeRegions(im2keys);
	freeDescriptors(im1desc);
	freeDescriptors(im2desc);
	freeMatches(matches);
	
	fprintf(stderr,"%04.2f %04.2f %04.2f\n",transform[0][0],transform[0][1],transform[0][2]);
	fprintf(stderr,"%04.2f %04.2f %04.2f\n",transform[1][0],transform[1][1],transform[1][2]);
	fprintf(stderr,"%04.2f %04.2f %04.2f\n",transform[2][0],transform[2][1],transform[2][2]);
	
	npy_intp dimensions[2];
	dimensions[0] = 3;
	dimensions[1] = 3;
	PyObject *pytransform = PyArray_SimpleNewFromData( 2, dimensions, NPY_DOUBLE, transform[0] );
	
	return pytransform;
	
}

static PyObject *PyFindRegions( PyObject *self, PyObject *args ) {
	
	PyObject *oim1;
	float minSize = 0.002, maxSize = 0.9, blur = 0.0, sharpen = 0.0;
	int U = TRUE, D = TRUE;
	if (!PyArg_ParseTuple(args, "Offffii", &oim1, &minSize, &maxSize, &blur, &sharpen, &U, &D)) goto fail;
	
	Image im1 = PyArrayToImage( oim1 );
	
	fprintf(stderr,"Converted from NumPy Array\n");
	
	PStack regions = NewPStack(1000);
	FindMSERegions(im1,regions,minSize,maxSize,blur,sharpen,U,D);
	
	fprintf(stderr,"Found %d regions.\n", regions->stacksize);
	
	PyObject *regionList = PyList_New(0);
	
	while ( !PStackIsEmpty(regions) ) {
		Region r = PopPStack(regions);
		PyObject *pyRegion = RegionToPyObject(r);
		PyList_Append(regionList,pyRegion);
	}
		
	FreeImage(im1);
	
	return Py_BuildValue("OO", regionList, Py_None);
	
	fail:
	Py_INCREF(Py_None);
	return Py_None;
	
}
 
static PyObject *PyPolygonVE( PyObject *self, PyObject *args ) {
	
	PyObject *vertices; float treshold = 0.1;
	if ( !PyArg_ParseTuple(args, "Of", &vertices, &treshold ) ) return Py_None;
	
	Polygon poly = PyArrayToPolygon( vertices );
	
	PolygonVertexEvolution( poly, treshold );
	
	return PolygonToPyArray(poly);
	
}
	
static Polygon PyArrayToPolygon( PyObject *object ) {
	
	Polygon poly = NULL;
	
	PyObject *vertices = PyArray_FROM_OTF(object,NPY_FLOAT,NPY_IN_ARRAY|NPY_FORCECAST);
	if ( vertices == NULL ) goto fail;
	
	if ( PyArray_NDIM(vertices) < 2 ) goto fail;
	
	int i, size = PyArray_DIM(vertices,1);
	
	float *x = (float *)PyArray_DATA(vertices);
	float *y = x + size;
	
	poly = NewPolygon(size);
	if ( poly == NULL ) goto fail;
	
	Point p = poly->vertices;
	poly->numberOfVertices = size;
	
	for (i=0;i<size;i++) { p[i].x = x[i]; p[i].y = y[i]; } 
	
	fail:
	
	Py_DECREF(vertices);
	return poly;
	
}

static PyObject *PyPolygonACD( PyObject *self, PyObject *args ) {
	// Just a placeholder for now
	Py_INCREF(Py_None);
	return Py_None;
}
	
static Image PyArrayToImage( PyObject *image ) {
	
	Image newImage = NULL;
	
	PyObject * py_array = PyArray_FROM_OTF(image,NPY_FLOAT,NPY_IN_ARRAY|NPY_FORCECAST);
	if ( py_array == NULL ) goto fail;
	
	if ( PyArray_NDIM(image) != 2 ) goto fail;
	
	int rows = PyArray_DIM(image,0);
	int cols = PyArray_DIM(image,1);

	newImage = CreateImage(rows,cols);
	if ( newImage == NULL ) goto fail;
	
	float *input = (float *)PyArray_DATA(image);
	int  *output = newImage->pixels[0];
	
	if ( input == NULL || output == NULL ) goto fail;
	
	int k;
	for (k=0;k<rows*cols;k++) {
		float pixel = input[k];
		if ( isnan(pixel) || isinf(pixel) ) pixel = 0.0;
		output[k] = pixel;	
	}
	
	Py_DECREF(py_array);
	
	return newImage;
	
	fail:
	fprintf(stderr,"Conversion from NumPy failed\n");
	FreeImage(newImage);
	Py_DECREF(py_array);
	return NULL;
	
}	

static PyObject *ImageToPyArray( Image image ) {
	
	if ( image == NULL ) goto fail;
	
	npy_intp dimensions[2];
	dimensions[0] = image->rows;
	dimensions[1] = image->cols;
	void * pixels = image->pixels[0];
	if ( pixels == NULL ) goto fail;
	
	PyObject *array = PyArray_SimpleNewFromData( 2, dimensions, NPY_INT, pixels );
	return array;
	
	fail:
	
	Py_INCREF(Py_None);
	return Py_None;
	
}

static PyObject *RegionToPyObject( Region r ) {
	
	PyObject *ellipseParameters, *pyRegion;
	PyObject *borderPoints;
	
	ellipseParameters = Py_BuildValue("fffffffffff",r->row,r->col,r->maj,r->min,r->phi,r->A,r->B,r->C,r->D,r->E,r->F);
	borderPoints = PolygonToPyArray( r->border );
	
	pyRegion  = Py_BuildValue("{s:O,s:O}","regionEllipse",ellipseParameters,"regionBorder",borderPoints);
	Py_XDECREF(ellipseParameters); Py_XDECREF(borderPoints);
	
	return pyRegion;
	
}

static PyObject *PolygonToPyArray( Polygon poly ) {
	
	float *data = NULL;
	
	if ( poly == NULL ) goto fail;

	int i, size = poly->numberOfVertices;
	if ( size == 0 ) goto fail;
	
	Point v = poly->vertices;
	
	data = malloc(sizeof(float)*size*2);
	if ( data == NULL ) goto fail;
	
	float *x = data;
	float *y = data + size;
	
	for (i=0;i<size;i++) { x[i] = v[i].x; y[i] = v[i].y; }
	
	npy_intp dimensions[2];
	dimensions[0] = 2;
	dimensions[1] = size;
	
	return PyArray_SimpleNewFromData( 2, dimensions, NPY_FLOAT, x );
	
	fail:
	if (data) free(data);
	Py_INCREF(Py_None);
	return Py_None;
	
}
	
static PyMethodDef libCVMethods[] = {
	{"MatchImages", PyMatchImages, METH_VARARGS, "BLANK"},
	{"FindRegions", PyFindRegions, METH_VARARGS, "BLANK"},
	{"PolygonVE", PyPolygonVE, METH_VARARGS, "BLANK"},
	{NULL, NULL}
};

PyMODINIT_FUNC initlibCV() {
	(void) Py_InitModule("libCV", libCVMethods);
	import_array()
}

