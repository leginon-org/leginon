#include <Python.h>
#include <numarray/libnumarray.h>
#include <math.h>

#include "point.h"
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

#ifndef MAX_DIM
#define MAX_DIM     6
#endif
/* #define DEBUG_RESAMPLEARRAY */
static PyObject *resamplearray(PyObject *self, PyObject *args) {
	PyObject *input1, *input2;
	PyArrayObject *inputarray=NULL, *scalerarray=NULL, *outputarray=NULL;
        float *resampled=NULL;
        int *newdims;
        int i;

	if(!PyArg_ParseTuple(args, "OO", &input1, &input2))
           return NULL;

	inputarray = NA_InputArray(input1, tFloat32, NUM_C_ARRAY|NUM_COPY);
        if (inputarray == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to accept a multidimensional array of type FLOAT.\n");
           return NULL;
        }

	scalerarray = NA_InputArray(input2, tFloat32, NUM_C_ARRAY|NUM_COPY);
        if (scalerarray == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to accept a one-dimensional array of type FLOAT as scaling factors.\n");
           return NULL;
        }
        if (inputarray->nd != scalerarray->dimensions[0]) {
           PyErr_SetString(PyExc_ValueError, "number of dimensions NOT equal to number of scaling factors.\n");
           return NULL;
        }
  
        newdims = (int *)calloc(inputarray->nd, sizeof(int));
        if (newdims == NULL) {
           PyErr_SetString(PyExc_ValueError, "failed to alloc space for newdims.\n");
           return NULL;
        }
        fresammpling_vector((float *)inputarray->data, inputarray->nd, (int *)inputarray->dimensions, 
                            &resampled, newdims, (float *)scalerarray->data, LINEAR);
        
#ifdef DEBUG_RESAMPLEARRAY
       for(i=0; i<inputarray->nd; i++)
          fprintf(stderr, "olddims[%d]=%d\tnewdims[%d]=%d\n", i, inputarray->dimensions[i], i, newdims[i]);
#endif

	outputarray = NA_vNewArray(resampled, tFloat32, inputarray->nd, newdims); 

        if (newdims != NULL) free(newdims);
	Py_DECREF(inputarray);
	Py_DECREF(scalerarray);
	return NA_OutputArray(outputarray, tFloat32, 0);
}

static PyObject *cannyedge(PyObject *self, PyObject *args) {
	PyObject *input;
	PyArrayObject *inputarray=NULL, *outputarray=NULL;
	int i, j;
        unsigned pos, nelements;
	float sigma, tlow, thigh;
        unsigned char *image=NULL;
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
        canny(image, inputarray->dimensions[0], inputarray->dimensions[1], sigma, tlow, thigh, &edge, NULL);
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
	outputarray = NA_vNewArray(edge, tUInt8, inputarray->nd, inputarray->dimensions); 
	Py_DECREF(inputarray);
	return NA_OutputArray(outputarray, tUInt8, 0);
}


PyArrayObject *PyArray_ContiguousFromPointList(POINT_LIST *plist) 
{
       POINT *pt=NULL;
       int i,j, dimensions[2];
       PyArrayObject *outputarray=NULL;

       if (plist == NULL)
           return NULL;

       dimensions[0] = plist->num_elements;
       dimensions[1] = plist->head->dim;
       outputarray = NA_vNewArray(NULL, tFloat32, 2, dimensions);
       for (pt = plist->head,i=0; pt != NULL; pt=pt->next,i++) 
           for (j=0; j<dimensions[1]; j++)
	       *(float *)(outputarray->data + i*outputarray->strides[0] + j*outputarray->strides[1]) = (float)pt->x[j];
       
       return outputarray;
}


extern LIST_OF_POINT_LIST * connected_component_labeling8(unsigned char *img, int rows, int cols); 

static PyObject *componentlabeling(PyObject *self, PyObject *args)
{
	PyObject *input;
	PyArrayObject *inputarray=NULL;
	int i, j, rows, cols;
        unsigned char *edge=NULL;
        int iterations;
        LIST_OF_POINT_LIST *lp_list=NULL;
        POINT_LIST *plist=NULL;

        PyObject *components=NULL;
        PyArrayObject *newcomponent=NULL;

        if(!PyArg_ParseTuple(args, "O", &input))
           return NULL;

	inputarray = NA_InputArray(input, tUInt8, NUM_C_ARRAY|NUM_COPY);
        if (inputarray == NULL || inputarray->nd != 2) {
           PyErr_SetString(PyExc_ValueError, "failed to accept a 2-D array of type UBYTE.\n");
           return NULL;
        }
        edge = (unsigned char *)inputarray->data;
        rows = inputarray->dimensions[0];
        cols = inputarray->dimensions[1];

        iterations = 3;
        morph_dilation3x3 (edge, rows, cols, iterations);
        morph_erosion3x3 (edge, rows, cols, iterations);

        lp_list = connected_component_labeling8(edge, rows, cols);
        if (lp_list !=NULL) {
	   components = PyList_New(0);
           for (plist = lp_list->head; plist!=NULL; plist=plist->next) { 
               newcomponent = PyArray_ContiguousFromPointList(plist);
               if (newcomponent != NULL) {
                  if (PyList_Append(components, (PyObject *)newcomponent)) {
		      Py_DECREF(newcomponent);
	              return components;
	          }
               }
           }
        } 

        free_list_of_point_list(lp_list);
	Py_DECREF(inputarray);
	return components;
}

static PyObject *fitcircle2edges(PyObject *self, PyObject *args)
{
	PyObject *input;
	PyArrayObject *inputarray=NULL;
	int i, j, rows, cols;
        unsigned char *edge=NULL;
        int iterations;
        LIST_OF_POINT_LIST *lp_list=NULL;
        POINT_LIST *plist=NULL, *ptr;
        int ierr=1;                  /* ierr == 1 indicats failure of fitting a circle. */
        double cx=0., cy=0., r=0.;
        double cxold, cyold, rold;
        double norm;
        PyObject *crclparams=NULL;
        int iter, max_iterations=3;
        double diff;

        if(!PyArg_ParseTuple(args, "O", &input))
           return NULL;

	inputarray = NA_InputArray(input, tUInt8, NUM_C_ARRAY|NUM_COPY);
        if (inputarray == NULL || inputarray->nd != 2) {
           PyErr_SetString(PyExc_ValueError, "failed to accept a 2-D array of type UBYTE.\n");
           return NULL;
        }
        edge = (unsigned char *)inputarray->data;
        rows = inputarray->dimensions[0];
        cols = inputarray->dimensions[1];

        iterations = 3;
        morph_dilation3x3 (edge, rows, cols, iterations);
        morph_erosion3x3 (edge, rows, cols, iterations);

        lp_list = connected_component_labeling8(edge, rows, cols);
        if (lp_list !=NULL) {
           /* fit a circle to the longest list of points. */
           plist = lp_list->head;
           for (ptr = lp_list->head; ptr!=NULL; ptr = ptr->next)
               if (plist->num_elements < ptr->num_elements)
                   plist = ptr;

           /* fit a circle to the list of points and reach stable stutus. */                                                 iter = 0;
           diff = 1.0;
           norm = (double) rows;
           ierr = fit_circle_to_point_list(plist, &cx, &cy, &r, norm);
           if (!ierr) {  /* succeeded at first try then see if it is stable.  */
              while (diff >= 1.0 && iter < max_iterations) {
                   cxold = cx;
                   cyold = cy;
                   rold = r;
                   norm *= 2.0;
                   ierr = fit_circle_to_point_list(plist, &cx, &cy, &r, norm);
                   diff = 0.;
                   diff += (cx -cxold) * (cx - cxold); 
                   diff += (cy -cyold) * (cy - cyold); 
                   diff += (r -rold) * (r - rold); 
                   iter++;
              } 
           }
        }

        /* return circle parameters in a list. */
        crclparams = PyList_New(0);
        PyList_Append(crclparams, Py_BuildValue("i", ierr));
        PyList_Append(crclparams, PyFloat_FromDouble(cx));
        PyList_Append(crclparams, PyFloat_FromDouble(cy));
        PyList_Append(crclparams, PyFloat_FromDouble(r));

        free_list_of_point_list(lp_list);
	Py_DECREF(inputarray);
	return crclparams;
}

static struct PyMethodDef numeric_methods[] = {
	{"resamplearray", resamplearray, METH_VARARGS},
        {"cannyedge", cannyedge, METH_VARARGS}, 
        {"componentlabeling", componentlabeling, METH_VARARGS}, 
        {"fitcircle2edges", fitcircle2edges, METH_VARARGS}, 
	{NULL, NULL}
};

void initbeamfinder()
{
	(void) Py_InitModule("beamfinder", numeric_methods);
	import_libnumarray()
}

