#include <Python.h>
#include <numarray/libnumarray.h>
#include "geometry.h"
#include "util.h"
#include "image.h"
#include "mser.h"
#include "csift.h"
#include "match.h"
#include "lautil.h"

static Image PyArrayToImage( PyObject *object );
static PyObject *ImageToPyArray( Image image );

static PyObject *FArrayToPyArray( FArray array );

static PyObject *RegionToPyObject( Region r );

static Polygon PyArrayToPolygon( PyObject *object );
static PyObject *PolygonToPyArray( Polygon poly );

static PyObject *PyMatchImages(PyObject *self, PyObject *args) {

	PyObject *oim1, *oim2;
	float t0 = CPUTIME;
	
	fprintf(stderr,"Preparing images for Python wrapper:  ");
	
	float minSize = 0.002, maxSize = 0.9, blur = 0.0, sharpen = 0.0;
	int U = TRUE, D = TRUE;
	if (!PyArg_ParseTuple(args, "OOffffii", &oim1, &oim2, &minSize, &maxSize, &blur, &sharpen, &U, &D )) return NULL;
	
	Image im1 = PyArrayToImage( oim1 );
	Image im2 = PyArrayToImage( oim2 );
	
	fprintf(stderr,"Time: %2.2f seconds\n",CPUTIME-t0);
	
	PStack im1keys = NewPStack(100);
	PStack im1desc = NewPStack(100);
	PStack im2keys = NewPStack(100);
	PStack im2desc = NewPStack(100);
	PStack matches = NewPStack(100);
	
	t0 = CPUTIME;
	fprintf(stderr,"Image 1:  ");
	FindMSERegions(im1,im1keys,minSize,maxSize,blur,sharpen,U,D);
	fprintf(stderr,"Keypoints: %d  ",im1keys->stacksize);
	RegionsToSIFTDescriptors(im1keys,im1desc,4,8,41);
	fprintf(stderr,"Descriptors: %d  Time: %2.2f\n",im1desc->stacksize,CPUTIME-t0);
	
	t0 = CPUTIME;
	fprintf(stderr,"Image 2:  ");
	FindMSERegions(im2,im2keys,minSize,maxSize,blur,sharpen,U,D);
	fprintf(stderr,"Keypoints: %d  ",im2keys->stacksize);
	RegionsToSIFTDescriptors(im2keys,im2desc,4,8,41);
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

static PyObject *PyFindRegions( PyObject *self, PyObject *args ) {
	
	float t0 = CPUTIME;
	
	PyObject *oim1;
	float minSize = 0.002, maxSize = 0.9, blur = 0.0, sharpen = 0.0;
	int U = TRUE, D = TRUE, R = TRUE;
	if (!PyArg_ParseTuple(args, "Offffiii", &oim1, &minSize, &maxSize, &blur, &sharpen, &U, &D, &R )) return NULL;
	
	Image im1 = PyArrayToImage( oim1 );
	
	PStack regions = NewPStack(1000);
	FindMSERegions(im1,regions,minSize,maxSize,blur,sharpen,U,D);
	
	fprintf(stderr,"Found %d regions.\n", regions->stacksize);
	
	PyObject *regionList = PyList_New(0);
	
	while ( !PStackIsEmpty(regions) ) {
		Region r = PopPStack(regions);
		PyObject *pyRegion = RegionToPyObject(r);
		PyList_Append(regionList,pyRegion);
		Ellipse e = NewEllipse(r->row,r->col,r->maj,r->min,r->phi);
		DrawEllipse(e,im1,RandomColor(200)); free(e);
		FreePolygon(r->border); free(r);
	}
	
	PyObject *regionImage = ImageToPyArray(im1);
		
	FreeImage(im1);
	
	fprintf(stderr,"Total time: %2.2f\n",CPUTIME-t0);
	
	return Py_BuildValue("OO", regionList, regionImage );
	
}
 
static PyObject *PyPolygonACD( PyObject *self, PyObject *args ) {
	
	PyObject *vertices; float treshold = 0.1;
	if ( !PyArg_ParseTuple(args,"Of", &vertices, &treshold) ) return Py_None;
	
	Polygon poly = PyArrayToPolygon( vertices );
	
	Image out = CreateImage(1024,1024); DrawPolygon(poly,out,255); WritePPM("sect.ppm",out);
	
	fprintf(stderr,"Performing Decomposition\n");
	PStack decomp = NewPStack(10);
	PolygonACD( poly, treshold, decomp );
	FreePolygon( poly );
	
	fprintf(stderr,"Decomposed into %d pieces\n",decomp->stacksize);
	
	PyObject *polygonDecomposition = PyList_New(0);
	
	while ( !PStackIsEmpty(decomp) ) {
		poly = PopPStack(decomp);
		PyList_Append( polygonDecomposition, (PyObject *)PolygonToPyArray(poly) );
		DrawPolygon(poly,out,RandomColor(200));
		FreePolygon(poly);
	}
	
	FreePStack(decomp);
	
	WritePPM("sect.ppm",out); FreeImage(out);
	
	return polygonDecomposition;
	
}

static PyObject *PyPolygonVE( PyObject *self, PyObject *args ) {
	
	PyObject *vertices; float treshold = 0.1;
	if ( !PyArg_ParseTuple(args, "Of", &vertices, &treshold ) ) return Py_None;
	
	Polygon poly = PyArrayToPolygon( vertices );
	
	PolygonVertexEvolution( poly, treshold );
	
	return PolygonToPyArray(poly);
	
}
	
static Polygon PyArrayToPolygon( PyObject *object ) {
	
	PyArrayObject *vertices = NA_InputArray(object,tFloat32,NUM_C_ARRAY);

	int i, size = vertices->dimensions[1];
	
	float *x = NA_OFFSETDATA(vertices);
	float *y = x + size;
	
	Polygon poly = NewPolygon(size);
	Point p = poly->vertices;
	
	for (i=0;i<size;i++) { p[i].x = x[i]; p[i].y = y[i]; } 
	
	Py_XDECREF( vertices );
	
	poly->numberOfVertices = size;
	
	return poly;

}
	
	
static Image PyArrayToImage( PyObject *image ) {
	
	PyArrayObject *temp = NA_InputArray(image,tInt32,NUM_C_ARRAY);
	
	int maxrow = temp->dimensions[0];
	int maxcol = temp->dimensions[1];
	
	Image newImage = CreateImage(maxrow,maxcol);
	memcpy(newImage->pixels[0],NA_OFFSETDATA(temp),sizeof(tInt32)*maxrow*maxcol);
	
	Py_XDECREF( temp );
	
	return newImage;
	
}	

static PyObject *ImageToPyArray( Image image ) {
	int maxrow = image->rows;
	int maxcol = image->cols;
	return (PyObject *)NA_NewArray(image->pixels[0], tInt32, 2, maxrow, maxcol );
}

static PyObject *FArrayToPyArray( FArray array ) {
	
	int rows = FArrayRows(array);
	int cols = FArrayCols(array);
	
	float *buffer = malloc(sizeof(tFloat32)*rows*cols);
	float **values = array->values;
	
	int row, col, count = 0;
	for (row=array->minrow;row<=array->maxrow;row++) {
		for (col=array->mincol;col<=array->maxcol;col++) {
			buffer[count++] = values[row][col];
	}}
	
	PyObject *pyarray = (PyObject *)NA_NewArray(buffer, tFloat32, 2, rows, cols );
	
	free(buffer);

	return pyarray;
	
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
	
	if ( poly == NULL ) return Py_None;
	int i, size = poly->numberOfVertices;
	if ( size == 0 ) return Py_None;
	Point v = poly->vertices;
	
	float *x = malloc(sizeof(float)*size*2);
	float *y = x + size;
	
	for (i=0;i<size;i++) { x[i] = v[i].x; y[i] = v[i].y; }
	
	return (PyObject *)NA_NewArray(x,tFloat32,2,2,size);
	
}
	

static PyMethodDef libCVMethods[] = {
	{"MatchImages", PyMatchImages, METH_VARARGS, "BLANK"},
	{"FindRegions", PyFindRegions, METH_VARARGS, "BLANK"},
	{"PolygonACD", PyPolygonACD, METH_VARARGS, "BLANK"},
	{"PolygonVE", PyPolygonVE, METH_VARARGS, "BLANK"},
	{NULL, NULL}
};

void initlibCV()
{
	(void) Py_InitModule("libCV", libCVMethods);
	import_libnumarray()
}

