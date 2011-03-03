/*
 *  allstats is a function to replace the numpy functions:
 *  	min(), max(), mean(), std()
 *	See README.allstats to see why.
 */

#include <Python.h>

typedef struct stats_struct {
	/* switch stat calculations on/off */
	int switch_min;
	int switch_max;
	int switch_mean;
	int switch_std;

	/* results */
	double n;
	double min;
	double max;
	double mean;
	double variance;
	double variance_n;
	double std;
	double m2;
} stats;

void initStats(stats *s);
void updateStats(stats *s, double new_value);
void allstats_byte(PyObject *inputarray, stats *result);
void allstats_ubyte(PyObject *inputarray, stats *result);
void allstats_short(PyObject *inputarray, stats *result);
void allstats_ushort(PyObject *inputarray, stats *result);
void allstats_int(PyObject *inputarray, stats *result);
void allstats_uint(PyObject *inputarray, stats *result);
void allstats_long(PyObject *inputarray, stats *result);
void allstats_ulong(PyObject *inputarray, stats *result);
void allstats_longlong(PyObject *inputarray, stats *result);
void allstats_ulonglong(PyObject *inputarray, stats *result);
void allstats_float(PyObject *inputarray, stats *result);
void allstats_double(PyObject *inputarray, stats *result);
void allstats_longdouble(PyObject *inputarray, stats *result);
PyObject * allstats(PyObject *self, PyObject *args, PyObject *kw);
