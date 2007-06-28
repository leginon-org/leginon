#include <Python.h>
#include <numarray/libnumarray.h>
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
static PyObject *FArrayToPyArray( FArray array );
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

static PyObject *PyDOG(PyObject *self, PyObject *args) {
	
	PyObject *image;
	int bin       = 4;
	int start     = 2;
	int end       = 10000;
	int sampling  = 5;
	float minT    = 0;
	float maxT    = 0;
	char stable   = FALSE;
	char debug    = FALSE;
	
	if ( !PyArg_ParseTuple(args,"Oiiiiffbb",&image,&bin,&start,&end,&sampling,&minT,&maxT,&stable,&debug) ) return NULL;
	
	fprintf(stderr,"Binning: %d   Range: %d-%d,%d\n",bin,start,end,sampling);
	fprintf(stderr,"Output: %d   Scale Stable:  %d\n",debug,stable);
	
	int c, cols = PyArray_DIMS(image)[0];
	int r, rows = PyArray_DIMS(image)[1];
	int max = rows*cols;
	float *p1 = malloc(sizeof(tFloat32)*max);
	memcpy(p1,PyArray_DATA(image),max*sizeof(tFloat32));

	
	BinFMatrix(p1,rows,cols,bin);
	rows /= bin;
	cols /= bin;
	
	max = rows*cols;
	
	int k; char name[256];

	for (k=0;k<max;k++) p1[k] *= -1;
	float *bak = malloc(sizeof(float)*max);
	for(k=0;k<max;k++) bak[k] = p1[k];

	float sigmaInterval = pow(2.0,1.0/sampling);
	float sigmaStep = sqrt(sigmaInterval-1.0);
	float sigma = start;
	
	int levels = end;
	float **scaleSpace = malloc(sizeof(float *)*levels);
	
	float blurs[levels];
	for (k=0;k<levels;k++) {
		blurs[k] = sigma*sigmaStep;
		sigma *= sigmaInterval;
	}
	fprintf(stderr,"Building ScaleSpace...");
	for (k=0;k<levels;k++) {
		float *p2 = GaussianBlurF(p1,rows,cols,blurs[k]);
		SubtractF(p1,p2,max);
		scaleSpace[k] = p1;
		p1 = p2;
	}
	fprintf(stderr,"DONE\n");
	
	int count = 0; Image im2 = NULL;
	FArray peaks = NewFArray(0,0,3,100);
	
	fprintf(stderr,"Scanning scalespace...");
	for (k=1;k<levels-1;k++) {
		if ( debug ) {
			im2 = FMatrixToImage(bak,rows,cols);
			sprintf(name,"V%03d.pgm",k);
		}
		float *l1 = scaleSpace[k];
		float *l2 = scaleSpace[k-1];
		float *l3 = scaleSpace[k+1];
		for (r=1;r<rows-1;r++) {
			for (c=1;c<cols-1;c++) {
				float val = l1[r*cols+c];
				if ( val < minT ) continue;
				if ( val > maxT ) continue;
				if ( !IsMinPeak(l1,r*cols+c,cols,val) ) continue;
				if ( stable && l2[r*cols+c] >= val ) continue;
				if ( stable && l3[r*cols+c] >= val ) continue;
				SetFArray(peaks,0,count,r);
				SetFArray(peaks,1,count,c);
				SetFArray(peaks,2,count,val);
				SetFArray(peaks,3,count,k);
				if ( debug ) {
					Ellipse newEllipse = NewEllipse(r,c,blurs[k]*3,blurs[k]*3,0);
					DrawEllipse(newEllipse,im2,255);
					free(newEllipse);
				}
				count++;
			}
		}
		if ( debug ) {
			WritePGM(name,im2);
			FreeImage(im2);
		}
	}
	fprintf(stderr,"DONE\n");
	if ( debug ) fprintf(stderr,"Output images written\n");
	
	for(k=0;k<levels;k++) free(scaleSpace[k]);
	free(scaleSpace);
	
	return FArrayToPyArray(peaks);
	
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
	
	//fprintf(stderr,"Image 1:  ");
	FindMSERegions(im1,im1keys,minSize,maxSize,blur,sharpen,U,D);
	//fprintf(stderr,"Keypoints: %d  ",im1keys->stacksize);
	RegionsToSIFTDescriptors(im1keys,im1desc,4,8,41);
	//fprintf(stderr,"Descriptors: %d\n",im1desc->stacksize);
	fprintf(stderr,"Image 1: keypoints: %d; descriptors: %d\n",im1keys->stacksize,im1desc->stacksize);
	
	//fprintf(stderr,"Image 2:  ");
	FindMSERegions(im2,im2keys,minSize,maxSize,blur,sharpen,U,D);
	//fprintf(stderr,"Keypoints: %d  ",im2keys->stacksize);
	RegionsToSIFTDescriptors(im2keys,im2desc,4,8,41);
	//fprintf(stderr,"Descriptors: %d\n",im2desc->stacksize);
	fprintf(stderr,"Image 2: keypoints: %d; descriptors: %d\n",im2keys->stacksize,im2desc->stacksize);

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
	
	PyObject *oim1;
	float minSize = 0.002, maxSize = 0.9, blur = 0.0, sharpen = 0.0;
	int U = TRUE, D = TRUE;
	if (!PyArg_ParseTuple(args, "Offffii", &oim1, &minSize, &maxSize, &blur, &sharpen, &U, &D)) return NULL;
	
	Image im1 = PyArrayToImage( oim1 );
	
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
	
	int maxrow = PyArray_DIMS(image)[0];
	int maxcol = PyArray_DIMS(image)[1];
	
	float *input = PyArray_DATA(image);
	
	Image newImage = CreateImage(maxrow,maxcol);
	
	int k;
	for (k=0;k<maxrow*maxcol;k++) newImage->pixels[k] = input[k];
	
	return newImage;
	
}	

static PyObject *ImageToPyArray( Image image ) {
	int maxrow = image->rows;
	int maxcol = image->cols;
	PyObject *temp = (PyObject *)NA_NewArray(image->pixels[0], tInt32, 2, maxrow, maxcol );
	return temp;
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
	{"DOG", PyDOG, METH_VARARGS, "BLANK"},
	{NULL, NULL}
};

void initlibCV() {
	(void) Py_InitModule("libCV", libCVMethods);
	import_libnumarray()
}

