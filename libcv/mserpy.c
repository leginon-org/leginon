#include <Python.h>
#include <numarray/libnumarray.h>
#include "defs.h"

Image PyArrayObjectToImage( PyArrayObject *array );

static PyObject *pyFindClusters(PyObject *self, PyObject *args) {

	PyObject *oim1, *oim2;
	PyArrayObject *im1pix, *im2pix;
	
	int minsize = 40;
	int maxsize = 1000000;
	int minperiod = 5;
	float minstable = 0.02;
	float t0 = 0;
	
	t0 = CPUTIME;
	fprintf(stderr,"Preparing images for Python wrapper:  ");
	if (!PyArg_ParseTuple(args, "OO", &oim1, &oim2)) return NULL;
	
	im1pix = NA_InputArray(oim1, tInt32, NUM_C_ARRAY);
	im2pix = NA_InputArray(oim2, tInt32, NUM_C_ARRAY);

	Image im1 = PyArrayObjectToImage( im1pix );
	Image im2 = PyArrayObjectToImage( im2pix );
	
	//EnhanceImage(im1,0,255,0.01,0.01);
	//EnhanceImage(im2,0,255,0.01,0.01);

	fprintf(stderr,"Time: %2.2f seconds\n",CPUTIME-t0);
	
	PStack im1keys = NewPStack(100);
	PStack im1desc = NewPStack(100);
	PStack im2keys = NewPStack(100);
	PStack im2desc = NewPStack(100);
	PStack matches = NewPStack(100);
	
	t0 = CPUTIME;
	fprintf(stderr,"Image 1:  ");
	CreateMSERKeypoints(im1,im1keys,minsize,maxsize,minperiod,minstable);
	fprintf(stderr,"Keypoints: %d  ",im1keys->stacksize);
	KeypointsToDescriptors(im1keys,im1desc,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Descriptors: %d  Time: %2.2f\n",im1desc->stacksize,CPUTIME-t0);
	
	t0 = CPUTIME;
	fprintf(stderr,"Image 2:  ");
	CreateMSERKeypoints(im2,im2keys,minsize,maxsize,minperiod,minstable);
	fprintf(stderr,"Keypoints: %d  ",im2keys->stacksize);
	KeypointsToDescriptors(im2keys,im2desc,TRUE,FALSE,FALSE,TRUE,TRUE,4,8,FALSE);
	fprintf(stderr,"Descriptors: %d  Time: %2.2f\n",im2desc->stacksize,CPUTIME-t0);
	
	double **transform = AllocDMatrix(3,3,0,0);
	FindMatches(im1desc,im2desc,matches,40);
	ScreenMatches(matches,transform);
	
	Py_XDECREF(im1pix);
	Py_XDECREF(im2pix);
	FreeImage(im1);
	FreeImage(im2);
	
	return NA_NewArray((void *)transform[0],tFloat64, 2, 3, 3);
	
}

Image PyArrayObjectToImage( PyArrayObject *array ) {

	int maxrow = array->dimensions[0];
	int maxcol = array->dimensions[1];
	
	Image newimage = CreateImage(maxrow,maxcol);
	
	memcpy(newimage->pixels[0],array->data,sizeof(int)*maxrow*maxcol);
	
	return newimage;
	
}

static struct PyMethodDef methods[] = {
	{"findclusters", pyFindClusters, METH_VARARGS},
	{NULL, NULL}
};

void initmser()
{
	(void) Py_InitModule("mser", methods);
	import_libnumarray()
}

