
#include <Python.h>
#include <Numeric/arrayobject.h>


void
print_array_info(PyArrayObject *array)
{
	int i, j, ndata;
	int nd, *dimensions, *strides;
	char *data;
	double *myptr;

	nd = array->nd;
	dimensions = array->dimensions;
	strides = array->strides;
	data = array->data;

	printf("number of dimensions:  %d\n", nd);
	printf("dimensions: ");
	for(i=0; i<nd; i++) {
		printf(" %d", dimensions[i]);
	}
	printf("\n");
	printf("strides: ");
	for(i=0; i<nd; i++) {
		printf(" %d", strides[i]);
	}
	printf("\n");

	ndata = 1;
	for(i=0; i<nd; i++) {
		ndata *= dimensions[i];
	}
	printf("total number of elements:  %d\n", ndata);


	printf("data: ");
	myptr = (double *)data;
	for(i=0; i<ndata; i++) {
			printf(" %f", myptr[i]);
	}
	printf("\n");

	/* alter the data */
	myptr = (double *)data;
	for(i=0; i<ndata; i++) {
			myptr[i] += 1.0;
			printf(" %f", myptr[i]);
	}


	printf("data again: ");
	myptr = (double *)data;
	for(i=0; i<dimensions[0]; i++) {
		for(j=0; j<dimensions[1]; j++) {
			printf(" %f", myptr[i*dimensions[1]+j]);
		}
	}
	printf("\n");


	return;
}

void
num_add_piece(target,source,gxoff,gyoff,theta,sclx,scly,thresh,gxmin,gxmax,gymin,gymax)
	PyArrayObject *target, *source;
	float gxoff, gyoff; /* coordinates of center of image */
	float theta;  /* angle between goniometer and image x axis */
	float sclx, scly;  /* pixel size */
	float thresh;
	float gxmin, gxmax, gymin, gymax;
{

	double *gimg, *img;
	int gnx, gny, gnpix, nx, ny;
	float resx, resy;
	float gxrnge, gyrnge;
	int i,j;
	int icnt, igcnt, igx, igy;
	float x, y, gx, gy, gx2, gy2;
	float sintheta, costheta;
   
	/*  old viewit stuff
	gimg= ss1->fdat;
	gnx= ss1->nn[0];
	gny= ss1->nn[1];
	gnpix= gnx*gny;
	gxrnge= gxmax- gxmin;  
	gyrnge= gymax- gymin;
	*/

	gimg = (double *)target->data;
 	gnx = target->dimensions[0];
 	gny = target->dimensions[1];
	gnpix = gnx * gny;
	gxrnge = gxmax - gxmin;
	gyrnge = gymax - gymin;

	/*  old viewit stuff
	img= ss2->fdat; 
	nx= ss2->nn[0];
	ny= ss2->nn[1];
	*/

	img = (double *)source->data;
	nx = source->dimensions[0];
	ny = source->dimensions[1];

	resx=  1.0/(2.0*(float) nx) -0.5 ;
	resy= 1.0/(2.0* (float) ny) - 0.5 ;
	sintheta= sin(theta);
	costheta= cos(theta);
	for (j=0; j< ny; j++) {
		y=  (float) j / (float) ny + resy;
		for (i=0; i<nx; i++) {
			icnt= j*nx +i;
			x=  (float) i / (float) nx + resx; 
			gx=  x*costheta + y *sintheta;
			gy=  x*sintheta - y *costheta;
			gx= nx*sclx*gx+gxoff;
			gy= ny*scly*gy+gyoff;
			igx= gnx* (gx-gxmin)/gxrnge;
			igy= gny* (gy-gymin)/gyrnge;
			igcnt= igy*gnx+igx;
			if ((igcnt >0) && (igcnt < gnpix) &&(img[icnt] > thresh )) gimg[igcnt]= img[icnt];
        
		}
	}
}


static PyObject *
add_piece(PyObject *self, PyObject *args)
{
	PyObject *mosaicob, *pieceob;
	PyArrayObject *mosaic, *piece;

	float gxoff, gyoff, theta, sclx, scly, thresh;
	float gxmin, gxmax, gymin, gymax;

	if (!PyArg_ParseTuple(args, "O!Offffffffff", &PyArray_Type, &mosaic, &pieceob,&gxoff,&gyoff,&theta,&sclx,&scly,&thresh,&gxmin,&gxmax,&gymin,&gymax))
		return NULL;

	if (mosaic->nd != 2 || mosaic->descr->type_num != PyArray_DOUBLE) {
		PyErr_SetString(PyExc_ValueError, "array must be two-dimensional and of type float");
		return NULL;
	}


	/* create proper PyArrayObjects from input source */
	piece = (PyArrayObject *)
		PyArray_ContiguousFromObject(pieceob, PyArray_DOUBLE, 2, 2);
	if (piece == NULL) return NULL;


	/*
	print_array_info(mosaic);
	*/
	num_add_piece(mosaic,piece,gxoff,gyoff,theta,sclx,scly,thresh,gxmin,gxmax,gymin,gymax);

	Py_DECREF(piece);

	return Py_BuildValue("");
}

static struct PyMethodDef mosaic_methods[] = {
	{"add_piece", add_piece, METH_VARARGS},
	{NULL, NULL}
};

void initmosaic()
{
	(void) Py_InitModule("mosaic", mosaic_methods);
	import_array()
}
