#include "main.h"

static struct PyMethodDef numeric_methods[] = {
	{"willsq", willsq, METH_VARARGS},
	{"tiltang", tiltang, METH_VARARGS},
	{"transform", transform, METH_VARARGS},
	{"radonshift", radonShiftCorrelate, METH_VARARGS},
	{"getAngles", getAngles, METH_VARARGS},
	{NULL, NULL} /* marks the end of this structure */
};

void initradermacher() {
	(void) Py_InitModule("radermacher", numeric_methods);
	import_array();
}
