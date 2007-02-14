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

#ifndef MAX_DIM
#define MAX_DIM     6
#endif

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

