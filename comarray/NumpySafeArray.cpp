#include <Python.h>
#include <numpy/arrayobject.h>
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

	PyObject *result;
	char type;
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
			type = NPY_INT16;
			break;
		case VT_I4:
			type = NPY_INT32;
			break;
		case VT_R4:
			type = NPY_FLOAT32;
			break;
		case VT_R8:
			type = NPY_FLOAT64;
			break;
		default:
			PyErr_SetString(PyExc_RuntimeError, "Invalid image type");
			return NULL;
	}

	int cdims = psaImage->cDims;
	dims = new npy_intp[cdims];
	size_t nbytes=1, elemsize;
	for(int i = 0; i < cdims; i++)
	{
		dims[i] = (npy_intp)psaImage->rgsabound[i].cElements;
		nbytes *= dims[i];
	}
	elemsize = SafeArrayGetElemsize(psaImage);
	nbytes = dims[0] * dims[1] * elemsize;
	result = PyArray_SimpleNew(cdims, dims, type);
	memcpy(PyArray_DATA(result), pbuffer, nbytes);
	SafeArrayUnaccessData(psaImage);
	SafeArrayDestroy(psaImage);
	delete dims;

	//return result;
	return result;
}

static PyObject *prop(PyObject *self, PyObject *args) {
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

	hr = pIDispatch->Invoke(rgDispId[0], riid, lcid, DISPATCH_PROPERTYGET, &dispParams, &varResult, &excepInfo, &uArgErr);
	delete [] rgDispId;
	if (FAILED(hr)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to Invoke method");
		return NULL;
	}

	PY_INTERFACE_POSTCALL;

	PyObject *result;
	char type;
	int *dims;

	SAFEARRAY *psaImage = NULL;
	void HUGEP *pbuffer = NULL, *pbuffercopy=NULL;
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
			type = NPY_INT16;
			break;
		case VT_I4:
			type = NPY_INT32;
			break;
		case VT_R4:
			type = NPY_FLOAT32;
			break;
		case VT_R8:
			type = NPY_FLOAT64;
			break;
		default:
			PyErr_SetString(PyExc_RuntimeError, "Invalid image type");
			return NULL;
	}

	dims = new npy_intp[psaImage->cDims];
	size_t nbytes = 1;
	int e = 0;
	for(e = 0; e < psaImage->cDims; e++)
		dims[e] = (npy_intp)psaImage->rgsabound[e].cElements;
		nbytes *= dims[e];
		printf("DIM: %d\n", dims[e]);
	nbytes *= SafeArrayGetElemsize(psaImage);
	printf("NBYTES: %d\n", nbytes);
	pbuffercopy = malloc(nbytes);
	memcpy(pbuffercopy, pbuffer, nbytes);

	result = PyArray_SimpleNewFromData(psaImage->cDims, dims, type, pbuffercopy);
	SafeArrayUnaccessData(psaImage);
	SafeArrayDestroy(psaImage);
	delete dims;

	return result;
}

static struct PyMethodDef methods[] = {
	{"call", call, METH_VARARGS},
	{"prop", prop, METH_VARARGS},
	{NULL, NULL}
};

void initNumpySafeArray() {
	Py_InitModule("NumpySafeArray", methods);
	import_array()
}

