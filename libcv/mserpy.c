#include <Python.h>
#include <numarray/libnumarray.h>
#include "defs.h"

static Image PyObjectToImage( PyObject *object );
static PyObject *ImageToPyObject( Image image );
static PyObject *FArrayToPyObject( FArray array );
static FArray KeypointsPStackToFArray( PStack keys );

static PyObject *pyMatchImages(PyObject *self, PyObject *args) {

	PyObject *oim1, *oim2;

	float minsize = 0.002;
	float maxsize = 0.9;
	float minperiod = 0.02;
	float minstable = 0.02;
	float t0 = 0;
	
	t0 = CPUTIME;
	fprintf(stderr,"Preparing images for Python wrapper:  ");
	if (!PyArg_ParseTuple(args, "OOffff", &oim1, &oim2, &minsize, &maxsize, &minperiod, &minstable)) return NULL;
	
	Image im1 = PyObjectToImage( oim1 );
	Image im2 = PyObjectToImage( oim2 );
	
	EnhanceImage(im1,0,255,0.01,0.01);
	EnhanceImage(im2,0,255,0.01,0.01);

	fprintf(stderr,"Time: %2.2f seconds\n",CPUTIME-t0);
	
	PStack im1keys = NewPStack(100);
	PStack im1desc = NewPStack(100);
	PStack im2keys = NewPStack(100);
	PStack im2desc = NewPStack(100);
	PStack matches = NewPStack(100);
	
	t0 = CPUTIME;
	fprintf(stderr,"Image 1:  ");
	FindMSERegions(im1,im1keys,minsize,maxsize,minperiod,minstable);
	fprintf(stderr,"Keypoints: %d  ",im1keys->stacksize);
	RegionsToDescriptors(im1keys,im1desc,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Descriptors: %d  Time: %2.2f\n",im1desc->stacksize,CPUTIME-t0);
	
	t0 = CPUTIME;
	fprintf(stderr,"Image 2:  ");
	FindMSERegions(im2,im2keys,minsize,maxsize,minperiod,minstable);
	fprintf(stderr,"Keypoints: %d  ",im2keys->stacksize);
	RegionsToDescriptors(im2keys,im2desc,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Descriptors: %d  Time: %2.2f\n",im2desc->stacksize,CPUTIME-t0);
	
	double **transform = AllocDMatrix(3,3,0,0);
	FindMatches(im1desc,im2desc,matches,20);
	ScreenMatches(matches,transform);
	
	FreeImage(im1);
	FreeImage(im2);
	
	PyObject *pytransform = (PyObject *)NA_NewArray((void *)transform[0],tFloat64, 2, 3, 3);
	FreeDMatrix(transform,0,0);
	
	return pytransform;
	
}

static PyObject *pyFindRegions( PyObject *self, PyObject *args ) {
	
	float t0 = CPUTIME;
	
	PyObject *oim1;
	float minsize, maxsize, minperiod, minstable;
	
	if ( !PyArg_ParseTuple(args, "Offff", &oim1, &minsize, &maxsize, &minperiod, &minstable) ) return NULL;
	Image im1 = PyObjectToImage( oim1 );
	
	EnhanceImage(im1,0,255,0.01,0.01);
	
	PStack keys = NewPStack(1000);
	FindMSERegions(im1,keys,minsize,maxsize,minperiod,minstable);
	
	fprintf(stderr,"Found %d regions.\n", keys->stacksize);
	
	FArray keyarray = KeypointsPStackToFArray( keys );
	PyObject *pyarray = FArrayToPyObject( keyarray );
	
	fprintf(stderr,"Total time: %2.2f\n",CPUTIME-t0);
	
	FreeImage(im1);
	FreeFArray( keyarray );
	
	return pyarray;
	
}

static Image PyObjectToImage( PyObject *object ) {
	
	PyArrayObject *pixels = NA_InputArray(object,tInt32,NUM_C_ARRAY);
	
	int maxrow = pixels->dimensions[0];
	int maxcol = pixels->dimensions[1];
	
	Image newimage = CreateImage(maxrow,maxcol);
	
	memcpy(newimage->pixels[0],pixels->data,sizeof(tInt32)*maxrow*maxcol);
	
	Py_XDECREF( pixels );
	
	return newimage;
	
}	

static PyObject *ImageToPyObject( Image image ) {
	int maxrow = image->rows;
	int maxcol = image->cols;
	PyArrayObject *pyarray = NA_NewArray((void *)image->pixels[0], tInt32, 2, maxrow, maxcol );
	return (PyObject *)pyarray;
}

static PyObject *FArrayToPyObject( FArray array ) {
	
	int rows = FArrayRows(array);
	int cols = FArrayCols(array);
	
	float *buffer = malloc(sizeof(tFloat32)*rows*cols);
	float **values = array->values;
	
	int row, col, count = 0;
	for (row=array->minrow;row<=array->maxrow;row++) {
		for (col=array->mincol;col<=array->maxcol;col++) {
			buffer[count++] = values[row][col];
	}}
	
	PyArrayObject *pyarray = NA_NewArray((void*)buffer, tFloat32, 2, rows, cols );
	
	free(buffer);

	return (PyObject *)pyarray;
	
}

static FArray KeypointsPStackToFArray( PStack keys ) {

	FArray array = NewFArray(0,0,0,0);
	
	int count = 0;
	while ( !PStackEmpty(keys) ) {
		Region key = PopPStack(keys);
		SetFArray(array,count,0,key->row);
		SetFArray(array,count,1,key->col);
		SetFArray(array,count,2,key->maj);
		SetFArray(array,count,3,key->min);
		SetFArray(array,count,4,key->phi);
		SetFArray(array,count,5,key->A);
		SetFArray(array,count,6,key->B);
		SetFArray(array,count,7,key->C);
		SetFArray(array,count,8,key->D);
		SetFArray(array,count,9,key->E);
		SetFArray(array,count,10,key->F);
		free(key); count++;
	}
	
	FreePStack(keys);
	
	return array;
	
}
		

static PyMethodDef mserMethods[] = {
	{"matchImages", pyMatchImages, METH_VARARGS, "BLANK"},
	{"findRegions", pyFindRegions, METH_VARARGS, "BLANK"},
	{NULL, NULL}
};

void initmser()
{
	(void) Py_InitModule("mser", mserMethods);
	import_libnumarray()
}

