/* -*- C -*- */
/*
 * Copyright (c) 1997,1998 Massachusetts Institute of Technology
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

/* fftw.h -- system-wide definitions */


 /* Swig wrapper file (modified fftw.h and rfftw.h) by
  *  Travis Oliphant < Oliphant.Travis@altavista.net >
  *
  */

%module fftw
%{
#include "fftw.h"      /* This one has fftw_real = double */
#include "rfftw.h"
#include "Python.h"
#include "Numeric/arrayobject.h"
%}


%init %{
        import_array();
%}


%typemap(python,in) fftw_complex * {
  /* Make sure input is a NumPy array and a Complex Double */
  PyArrayObject *arr;
  if ((arr = (PyArrayObject *) PyArray_ContiguousFromObject($source, PyArray_CDOUBLE, 0, 0)) == NULL) return NULL;
  $target = (fftw_complex *)arr->data;
  $source = (PyObject *)arr;
}

%typemap(python,freearg) fftw_complex * {
  Py_XDECREF($arg); 
}  

%typemap(python,in) fftw_real * {
  /* Check to see if input is a NumPy array and if it is Double */
  PyArrayObject *arr;
  if ((arr = (PyArrayObject *) PyArray_ContiguousFromObject($source, PyArray_DOUBLE, 0, 0)) == NULL) return NULL;
  $target = (fftw_real *)arr->data;
  $source = (PyObject *)arr;
}

%typemap(python,freearg) fftw_real * {
  Py_XDECREF($arg);
}

%typemap(python,in) int * {
  /* Check to see if input is a NumPy array and if it is integer */
  PyArrayObject *arr;
  if ((arr = (PyArrayObject *) PyArray_ContiguousFromObject($source, PyArray_INT, 1, 1)) == NULL) return NULL;
  $target = (int *)arr->data;
  $source = (PyObject *)arr;
}

%typemap(python,freearg) int * {
  Py_XDECREF($arg);
}

%typemap(python,in) FILE * {
  if (!(PyFile_Check($source))) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a File");
        return NULL;
  }
  $target = PyFile_AsFile($source);
}

typedef enum {
     FFTW_FORWARD = -1, FFTW_BACKWARD = 1
} fftw_direction;


typedef enum {
     FFTW_SUCCESS = 0, FFTW_FAILURE = -1
} fftw_status;

/*
 * A configuration is a database of all known codelets
 */

enum fftw_node_type {
     FFTW_NOTW, FFTW_TWIDDLE, FFTW_GENERIC, FFTW_RADER,
     FFTW_REAL2HC, FFTW_HC2REAL, FFTW_HC2HC, FFTW_RGENERIC
};

typedef enum {
     FFTW_NORMAL_RECURSE = 0,
     FFTW_VECTOR_RECURSE = 1
} fftw_recurse_kind;

/* flags for the planner */
#define  FFTW_ESTIMATE (0)
#define  FFTW_MEASURE  (1)

#define FFTW_OUT_OF_PLACE (0)
#define FFTW_IN_PLACE (8)
#define FFTW_USE_WISDOM (16)

#define FFTW_THREADSAFE (128)  /* guarantee plan is read-only so that the
				  same plan can be used in parallel by
				  multiple threads */

#define FFTWND_FORCE_BUFFERED (256)     /* internal flag, forces buffering
                                           in fftwnd transforms */

#define FFTW_NO_VECTOR_RECURSE (512)    /* internal flag, prevents use
                                           of vector recursion */

extern fftw_plan fftw_create_plan_specific(int n, fftw_direction dir,
					   int flags,
					   fftw_complex *in, int istride,
					 fftw_complex *out, int ostride);
#define FFTW_HAS_PLAN_SPECIFIC
extern fftw_plan fftw_create_plan(int n, fftw_direction dir, int flags);
extern void fftw_print_plan(fftw_plan plan);
extern void fftw_destroy_plan(fftw_plan plan);
extern void fftw(fftw_plan plan, int howmany, fftw_complex *in, int istride,
		 int idist, fftw_complex *out, int ostride, int odist);
extern void fftw_one(fftw_plan plan, fftw_complex *in, fftw_complex *out);
extern void fftw_die(const char *s);
extern void fftw_check_memory_leaks(void);
extern void fftw_print_max_memory_usage(void);

extern size_t fftw_sizeof_fftw_real(void);

/* Wisdom: */
/*
 * define this symbol so that users know we are using a version of FFTW
 * with wisdom
 */
#define FFTW_HAS_WISDOM
extern void fftw_forget_wisdom(void);
extern void fftw_export_wisdom_to_file(FILE *output_file);
extern fftw_status fftw_import_wisdom_from_file(FILE *input_file);
extern char *fftw_export_wisdom_to_string(void);
extern fftw_status fftw_import_wisdom_from_string(const char *input_string);

#define FFTW_HAS_FPRINT_PLAN
extern void fftw_fprint_plan(FILE *f, fftw_plan plan);

extern fftwnd_plan fftw2d_create_plan(int nx, int ny, fftw_direction dir,
				      int flags);
extern fftwnd_plan fftw3d_create_plan(int nx, int ny, int nz,
				      fftw_direction dir, int flags);
extern fftwnd_plan fftwnd_create_plan(int rank, const int *n,
				      fftw_direction dir,
				      int flags);

extern fftwnd_plan fftw2d_create_plan_specific(int nx, int ny,
					       fftw_direction dir,
					       int flags,
					   fftw_complex *in, int istride,
					 fftw_complex *out, int ostride);
extern fftwnd_plan fftw3d_create_plan_specific(int nx, int ny, int nz,
					   fftw_direction dir, int flags,
					   fftw_complex *in, int istride,
					 fftw_complex *out, int ostride);
extern fftwnd_plan fftwnd_create_plan_specific(int rank, const int *n,
					       fftw_direction dir,
					       int flags,
					   fftw_complex *in, int istride,
					 fftw_complex *out, int ostride);

/* Freeing the FFTWND plan: */
extern void fftwnd_destroy_plan(fftwnd_plan plan);

/* Printing the plan: */
extern void fftwnd_fprint_plan(FILE *f, fftwnd_plan p);
extern void fftwnd_print_plan(fftwnd_plan p);
#define FFTWND_HAS_PRINT_PLAN

/* Computing the N-Dimensional FFT */
extern void fftwnd(fftwnd_plan plan, int howmany,
		   fftw_complex *in, int istride, int idist,
		   fftw_complex *out, int ostride, int odist);
extern void fftwnd_one(fftwnd_plan p, fftw_complex *in, fftw_complex *out);


/*
 * Copyright (c) 1997-1999 Massachusetts Institute of Technology
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 */

/* rfftw.h -- system-wide definitions for rfftw */


#define FFTW_REAL_TO_COMPLEX FFTW_FORWARD
#define FFTW_COMPLEX_TO_REAL FFTW_BACKWARD

extern void rfftw(rfftw_plan plan, int howmany, fftw_real *in, int istride,
		  int idist, fftw_real *out, int ostride, int odist);
extern void rfftw_one(rfftw_plan plan, fftw_real *in, fftw_real *out);
     
extern rfftw_plan rfftw_create_plan_specific(int n, fftw_direction dir,
					    int flags,
					    fftw_real *in, int istride,
					    fftw_real *out, int ostride);

extern rfftw_plan rfftw_create_plan(int n, fftw_direction dir, int flags);
extern void rfftw_destroy_plan(rfftw_plan plan);

extern void rfftw_fprint_plan(FILE *f, rfftw_plan p);
extern void rfftw_print_plan(rfftw_plan p);

extern void rfftw_executor_simple(int n, fftw_real *in,
				  fftw_real *out,
				  fftw_plan_node *p,
				  int istride,
				  int ostride,
				  fftw_recurse_kind recurse_kind);

extern rfftwnd_plan rfftwnd_create_plan_specific(int rank, const int *n,
						fftw_direction dir, int flags,
						fftw_real *in, int istride,
						fftw_real *out, int ostride);
extern rfftwnd_plan rfftw2d_create_plan_specific(int nx, int ny,
					   fftw_direction dir, int flags,
					      fftw_real *in, int istride,
					    fftw_real *out, int ostride);
extern rfftwnd_plan rfftw3d_create_plan_specific(int nx, int ny, int nz,
					   fftw_direction dir, int flags,
					      fftw_real *in, int istride,
					    fftw_real *out, int ostride);
extern rfftwnd_plan rfftwnd_create_plan(int rank, const int *n,
					  fftw_direction dir, int flags);
extern rfftwnd_plan rfftw2d_create_plan(int nx, int ny,
					  fftw_direction dir, int flags);
extern rfftwnd_plan rfftw3d_create_plan(int nx, int ny, int nz,
					  fftw_direction dir, int flags);
extern void rfftwnd_destroy_plan(rfftwnd_plan plan);
extern void rfftwnd_fprint_plan(FILE *f, rfftwnd_plan plan);
extern void rfftwnd_print_plan(rfftwnd_plan plan);
extern void rfftwnd_real_to_complex(rfftwnd_plan p, int howmany,
				   fftw_real *in, int istride, int idist,
			      fftw_complex *out, int ostride, int odist);
extern void rfftwnd_complex_to_real(rfftwnd_plan p, int howmany,
				fftw_complex *in, int istride, int idist,
				 fftw_real *out, int ostride, int odist);
extern void rfftwnd_one_real_to_complex(rfftwnd_plan p,
					fftw_real *in, fftw_complex *out);
extern void rfftwnd_one_complex_to_real(rfftwnd_plan p,
					fftw_complex *in, fftw_real *out);

