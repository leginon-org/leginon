#include <Python.h>
#include <numarray/libnumarray.h>

#define _WIN32_DCOM
#include <atlbase.h>

#import "c:\tecnai\plugins\tecnaiccd.dll" no_namespace

static PyObject *acquire(PyObject *self, PyObject *args) {
	PyArrayObject *result;
	NumarrayType type;
	int *dims;

	HRESULT hr;
	CComPtr<IGatanCamera> pCamera;
	SAFEARRAY *psaImage = NULL;
	_variant_t vTemp;
	void HUGEP *pbuffer = NULL;
	VARTYPE vartype;
	int left, top, right, bottom, binning;
	float exposuretime;

	if (!PyArg_ParseTuple(args, "iiiiif", &left, &top, &right, &bottom, &binning, &exposuretime))
		return NULL;

	// don't initialize com/create instance every acquire, will update
	// I also meant to set exceptions
	CoInitializeEx(NULL, COINIT_MULTITHREADED);

	hr = pCamera.CoCreateInstance(&(OLESTR("TecnaiCCD.GatanCamera")));
	if (FAILED(hr)) {
		PyErr_SetString(PyExc_RuntimeError, "Failed to initialize camera");
		return NULL;
	}

	pCamera->CameraLeft = left;
	pCamera->CameraTop = top;
	pCamera->CameraRight = right;
	pCamera->CameraBottom = bottom;
	pCamera->Binning = binning;
	pCamera->ExposureTime = exposuretime;

	vTemp = pCamera->AcquireRawImage();

	if (!(vTemp.vt & VT_ARRAY)) {
		PyErr_SetString(PyExc_RuntimeError, "Image is not an array");
		return NULL;
	}
	psaImage = vTemp.parray;

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
	delete dims;

	pCamera.Release();
	CoUninitialize();

	return (PyObject *)result;
}

static struct PyMethodDef methods[] = {
	{"acquire", acquire, METH_VARARGS},
	{NULL, NULL}
};

void initTecnaiCCDWrapper() {
	Py_InitModule("TecnaiCCDWrapper", methods);
	import_libnumarray()
}

