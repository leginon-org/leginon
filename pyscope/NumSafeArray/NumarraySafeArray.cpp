#include <Python.h>
#include <numarray/libnumarray.h>
#include <PythonCOM.h>

#define _WIN32_DCOM
#include <atlbase.h>

static PyObject *call(PyObject *self, PyObject *args) {
	PyObject *o, *pPyObject;
    const char *s;
	PyIDispatch *pPyIDispatch;
	IDispatch *pIDispatch;
	REFIID riid = IID_NULL;
	unsigned int cNames = 1;
	OLECHAR FAR* FAR* rgszNames = new LPOLESTR[cNames];
	LCID lcid = LOCALE_SYSTEM_DEFAULT;
	DISPID FAR* rgDispId = new DISPID[cNames];
	DISPPARAMS dispParams = {NULL, NULL, 0, 0};
	VARIANT varResult;
	EXCEPINFO excepInfo;
	unsigned int uArgErr;
	HRESULT hr;

	if (!PyArg_ParseTuple(args, "Os", &o, &s))
		return NULL;

    pPyObject = PyObject_GetAttrString(o, "_oleobj_");
	if (pPyObject == NULL) {
		PyErr_SetString(PyExc_AttributeError,
                         "no attribute _oleobj_ for dispatch");
		return NULL;
	}

    USES_CONVERSION;
	rgszNames[0] = A2OLE(s);

	pPyIDispatch = (PyIDispatch *)pPyObject;
	pIDispatch = pPyIDispatch->GetI(pPyIDispatch);

    Py_DECREF(pPyObject);

	PY_INTERFACE_PRECALL;

	hr = pIDispatch->GetIDsOfNames(riid, rgszNames, cNames, lcid, rgDispId);
	delete [] rgszNames;
	if (FAILED(hr)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to get DISPID");
		delete [] rgDispId;
		return NULL;
	}

	hr = pIDispatch->Invoke(rgDispId[0], riid, lcid, DISPATCH_METHOD, &dispParams, &varResult, &excepInfo, &uArgErr);
	delete [] rgDispId;
	if (FAILED(hr)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to Invoke method");
		return NULL;
	}

	PY_INTERFACE_POSTCALL;

	PyArrayObject *result;
	NumarrayType type;
	int *dims;

	SAFEARRAY *psaImage = NULL;
	void HUGEP *pbuffer = NULL;
	VARTYPE vartype;

	if (!(varResult.vt & VT_ARRAY)) {
		PyErr_SetString(PyExc_RuntimeError, "Image is not an array");
		return NULL;
	}
	psaImage = varResult.parray;

	hr = SafeArrayAccessData(psaImage, (void HUGEP* FAR*)&pbuffer);
	if (FAILED(hr)) {
		PyErr_SetString(PyExc_RuntimeError, "Access image data failed");
		return NULL;
	}

	SafeArrayGetVartype(psaImage, &vartype);

	switch(vartype) {
		case VT_I2:
			type = tInt16;
			break;
		case VT_I4:
			type = tInt32;
			break;
		case VT_R4:
			type = tFloat32;
			break;
		case VT_R8:
			type = tFloat64;
			break;
		default:
			PyErr_SetString(PyExc_RuntimeError, "Invalid image type");
			return NULL;
	}

	dims = new int[psaImage->cDims];
	for(int i = 0; i < psaImage->cDims; i++)
		dims[i] = (int)psaImage->rgsabound[i].cElements;

	result = NA_vNewArray(pbuffer, type, psaImage->cDims, dims);
	SafeArrayUnaccessData(psaImage);
	SafeArrayDestroy(psaImage);
	delete dims;

	return (PyObject *)result;
}

static struct PyMethodDef methods[] = {
	{"call", call, METH_VARARGS},
	{NULL, NULL}
};

void initNumSafeArray() {
	Py_InitModule("NumSafeArray", methods);
	import_libnumarray()
}

