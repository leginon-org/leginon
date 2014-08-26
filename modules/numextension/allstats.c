/*
 *  allstats is a function to replace the numpy functions:
 *  	min(), max(), mean(), std()
 *	See README.allstats to see why.
 */

#include <Python.h>

#define PY_ARRAY_UNIQUE_SYMBOL numextension_ARRAY_API
#define NO_IMPORT_ARRAY
#include <numpy/arrayobject.h>

#include "allstats.h"

/*
 * Initialize the stats structure.
 */
void initStats(stats *s) {
	s->switch_min = 0;
	s->switch_max = 0;
	s->switch_mean = 0;
	s->switch_std = 0;
	s->n = 0.0;
	s->min = 1e38;
	s->max = -1e38;
	s->mean = 0.0;
	s->variance = 0.0;
	s->variance_n = 0.0;
	s->std = 0.0;
	s->m2 = 0.0;
}

/*
 * Calculate new stats values from a new input value.
 * TODO: optimize min/max calculation by passing it two values at a
 *  time like in the existing numextension.minmax function.
 */
void updateStats(stats *s, double new_value) {
	double delta;

	if (s->switch_mean || s->switch_std) {
		s->n += 1;
		delta = new_value - s->mean;
		s->mean = s->mean + delta / s->n;
		if (s->switch_std) {
			s->m2 = s->m2 + delta * (new_value - s->mean);
			s->variance_n = s->m2 / s->n;
		}
	}

	/*  Not using this at the moment
	if(s->n > 1) {
		s->variance = s->m2 / (s->n - 1);
	} else {
		s->variance = INFINITY;
	}
	*/

	if (s->switch_max) {
		if (new_value > s->max) {
			s->max = new_value;
		}
	}
	if (s->switch_min) {
		if (new_value < s->min) {
			s->min = new_value;
		}
	}
}


/*
 * The following functions allstats_... are all similar.  They create an
 * iterator on the input array, then loop on the array calling updateStats
 * on each element.  The only difference between these functions is the
 * numpy array type they are expecting.  The data pointer must be cast
 * to that type, then dereferenced and cast to a double which updateStats
 * is expecting.
 */

void allstats_byte(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_byte *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_byte *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_ubyte(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_ubyte *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_ubyte *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_short(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_short *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_short *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_ushort(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_ushort *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_ushort *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_int(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_int *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_int *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_uint(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_uint *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_uint *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_long(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_long *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_long *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_ulong(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_ulong *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_ulong *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_longlong(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_longlong *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_longlong *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_ulonglong(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_ulonglong *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_ulonglong *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_float(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_float *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_float *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_double(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_double *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_double *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

void allstats_longdouble(PyObject *inputarray, stats *result) {
	PyObject *iter;
	npy_longdouble *ptr;

	iter = PyArray_IterNew(inputarray);

	while (PyArray_ITER_NOTDONE(iter)) {
		ptr = (npy_longdouble *)PyArray_ITER_DATA(iter);
		updateStats(result, (double) (*ptr));
		PyArray_ITER_NEXT(iter);
	}
	Py_XDECREF(iter);
}

/*
 * This is the main allstats function that will be exposed to python.
 * It parses the arguments, checks the numpy array type, then delegates to
 * one of the above allstats_... functions depending on type.
 */

PyObject * allstats(PyObject *self, PyObject *args, PyObject *kw) {
	static char *kwlist[] = {"input", "min", "max", "mean", "std", NULL};
	PyObject *input, *inputarray;
	PyObject *switch_min, *switch_max, *switch_mean, *switch_std;
	PyObject *outputdict, *value;
	int input_typenum;
	stats result;

	/* Parse input args.
	 * "input":  a numpy array or a python object that converts to an array.
	 * Optionally:  "min", "max", "mean", "std" truth values, which default to False
	 */
	switch_min = switch_max = switch_mean = switch_std = Py_None;
	if (!PyArg_ParseTupleAndKeywords(args, kw, "O|OOOO", kwlist, &input, &switch_min, &switch_max, &switch_mean, &switch_std))
		return NULL;

	/*
	 * Create proper PyArrayObject from input python object.
	 * This does the bare minimum to create a numpy array.  If the input
	 * python object is already a numpy array, then no copy will be made.
	 * It will not ensure contiguous, aligned, etc, so operations on the
	 * array object should account for that.
	 */
	inputarray = PyArray_FromAny(input, NULL, 0, 0, 0, NULL);
	if (inputarray == NULL) {
		Py_XDECREF(inputarray);
		return NULL;
	}

	/*
	 * Initialize the result and switch stats on/off depending on args
	 */
	initStats(&result);
	if (PyObject_IsTrue(switch_min))
		result.switch_min = 1;
	if (PyObject_IsTrue(switch_max))
		result.switch_max = 1;
	if (PyObject_IsTrue(switch_mean))
		result.switch_mean = 1;
	if (PyObject_IsTrue(switch_std))
		result.switch_std = 1;

	/*
	 * Delegate to type specific function.
	 */
	input_typenum = PyArray_TYPE(inputarray);
	switch (input_typenum) {
		case NPY_BYTE:
			allstats_byte(inputarray, &result);
			break;
		case NPY_UBYTE:
			allstats_ubyte(inputarray, &result);
			break;
		case NPY_SHORT:
			allstats_short(inputarray, &result);
			break;
		case NPY_USHORT:
			allstats_ushort(inputarray, &result);
			break;
		case NPY_INT:
			allstats_int(inputarray, &result);
			break;
		case NPY_UINT:
			allstats_uint(inputarray, &result);
			break;
		case NPY_LONG:
			allstats_long(inputarray, &result);
			break;
		case NPY_ULONG:
			allstats_ulong(inputarray, &result);
			break;
		case NPY_LONGLONG:
			allstats_longlong(inputarray, &result);
			break;
		case NPY_ULONGLONG:
			allstats_ulonglong(inputarray, &result);
			break;
		case NPY_FLOAT:
			allstats_float(inputarray, &result);
			break;
		case NPY_DOUBLE:
			allstats_double(inputarray, &result);
			break;
		case NPY_LONGDOUBLE:
			allstats_longdouble(inputarray, &result);
			break;
		case NPY_CFLOAT:
		case NPY_CDOUBLE:
		case NPY_CLONGDOUBLE:
		default:
			PyErr_Format(PyExc_TypeError, "no allstats support for typenum %d", input_typenum);
			Py_XDECREF(inputarray);
			return NULL;
	}
	Py_XDECREF(inputarray);

	/* Create return value:  a python dict containing the stats. */
	outputdict = PyDict_New();

	if (result.switch_min) {
		value = PyFloat_FromDouble(result.min);
		PyMapping_SetItemString(outputdict, "min", value);
		Py_XDECREF(value);
	}

	if (result.switch_max) {
		value = PyFloat_FromDouble(result.max);
		PyMapping_SetItemString(outputdict, "max", value);
		Py_XDECREF(value);
	}

	if (result.switch_mean) {
		value = PyFloat_FromDouble(result.mean);
		PyMapping_SetItemString(outputdict, "mean", value);
		Py_XDECREF(value);
	}

	/* Need final calculation of standard deviation from variance */
	if (result.switch_std) {
		result.std = sqrt(result.variance_n);
		value = PyFloat_FromDouble(result.std);
		PyMapping_SetItemString(outputdict, "std", value);
		Py_XDECREF(value);
	}
	return outputdict;
}
