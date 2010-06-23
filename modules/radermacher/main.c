#include "main.h"

static struct PyMethodDef numeric_methods[] = {
	{"willsq", willsq, METH_VARARGS},
	{"tiltang", tiltang, METH_VARARGS},
	{"transform", transform, METH_VARARGS},
	{NULL, NULL}
};

void initradermacher() {
	(void) Py_InitModule("radermacher", numeric_methods);
	import_array();
}
