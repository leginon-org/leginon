#include "main.h"
#include "Python.h"
#include "numpy/arrayobject.h"
#include <math.h>

/*
**
** Radon transform functions
**
*/

static struct item {
	int x;
	int y;
	double angle;
	struct item *next;
};

static void print_list(struct item *head) {
	struct item *current;
	for(current=head; current!=NULL; current=current->next) {
		fprintf(stderr, "%d,%d -- %.3f\n", current->x, current->y, current->angle);
	}
	return;
};

/*static int list_length(struct item *head) {
	struct item *current;
	current = head;
	int count=0;
	while (current != NULL) {
		count++;
		current = current->next;
	}
	return count;
};*/

static int list_length(struct item *head) {
	struct item *current;
	int count=0;
	for(current=head; current!=NULL; current=current->next) {
		count++;
	}
	return count;
};

static void delete_list(struct item *head) {
	struct item *current;
	current = head;
	while (current != NULL) {
		head = current;
		current = current->next;
		free (head);
	}
	return;
};


static struct item *add_to_list(int x, int y, struct item *head) {
	double angle = atan2(x, y);
	//printf("\nADD: %d,%d -- %.3f\n", x, y, angle);
	//print_list(head);

	struct item *current;
	if (head == NULL || angle < head->angle) {
		//printf("Allocating new head pointer\n");
		current = malloc(sizeof(struct item));
		current->x = x;
		current->y = y;
		current->angle = angle;
		current->next = head;
		head = current;
		return head;
	}
	current = head;
	int stop = 0;
	while (current != NULL && !stop) {
		if (angle >= current->angle && (current->next == NULL || angle < current->next->angle )) {
			stop = 1;
			//printf("Allocating new intermediate pointer for %.3f after %.3f\n", angle, current->angle);
			if (!(current->x == x && current->y == y)) {
				struct item *newitem;
				newitem = malloc(sizeof(struct item));
				newitem->x = x;
				newitem->y = y;
				newitem->angle = angle;
				//printf("%.3f\n", angle);
				newitem->next = current->next;
				current->next = newitem;
			}
		}
		current = current->next;
	}
	return head;
};

static struct item *getAnglesList(int radius, struct item *head) {
	//angle *head;
	//converted from http://en.wikipedia.org/wiki/Midpoint_circle_algorithm

	if (radius == 0) {
		head = add_to_list(0, 0, head);
		return head;
	}

	head = add_to_list(0,  radius, head);
	head = add_to_list(0, -radius, head);
	head = add_to_list( radius, 0, head);
	head = add_to_list(-radius, 0, head);
	if (radius <= 1) {
		return head;
	}

	int f = 1 - radius;
	int ddF_x = 1;
	int ddF_y = -2 * radius;
	int x = 0;
	int y = radius;
	while(x < y)
	{
		// ddF_x == 2 * x + 1;
		// ddF_y == -2 * y;
		// f == x*x + y*y - radius*radius + 2*x - y + 1;
		if(f >= 0)
		{
			y--;
			ddF_y += 2;
			f += ddF_y;
		}
		x++;
		ddF_x += 2;
		f += ddF_x;
		head = add_to_list( x,  y, head);
		head = add_to_list(-x,  y, head);
		head = add_to_list( x, -y, head);
		head = add_to_list(-x, -y, head);
		head = add_to_list( y,  x, head);
		head = add_to_list(-y,  x, head);
		head = add_to_list( y, -x, head);
		head = add_to_list(-y, -x, head);
	}

	return head;
}

PyObject* getAngles(PyObject *self, PyObject *args) {
/*
** Inputs:
** 	interger of search radius (in pixels)
** Modifies:
** 	nothing
** Outputs:
** 	1D numpy array containing correlation values of angle (x-axis)
*/
	Py_Initialize();
	int radius;
	if (!PyArg_ParseTuple(args, "i", &radius))
		return NULL;

	struct item *head = NULL;
	head = getAnglesList(radius, head);
	int numangles = list_length(head);

	npy_intp outdims[1] = {numangles};

	import_array(); // this is required to use PyArray_New() and PyArray_SimpleNew()
	PyArrayObject *output;
	output = (PyArrayObject *) PyArray_SimpleNew(1, outdims, NPY_DOUBLE);

	struct item *current;
	int i=0;
	for(current=head; current!=NULL; current=current->next) {
		*(double *) PyArray_GETPTR1(output, i) = current->angle;
		i++;
	}
	delete_list(head);

	return PyArray_Return(output);
}

PyObject* radonShiftCorrelate(PyObject *self, PyObject *args) {
/*
** Inputs:
** 	(1) 2D numpy array of first Radon transform (using doubles)
** 	(2) 2D numpy array of second Radon transform (using doubles)
** 	(3) interger of search radius (in pixels)
** Modifies:
** 	nothing
** Outputs:
** 	1D numpy array containing correlation values of angle (y-axis) and shift (x-axis)
*/
	Py_Initialize();

	/* Simple test loop */
	/*struct item *headtwo = NULL;
	int rad;
	for(rad=0; rad<8; rad++) {
		struct item *headtwo = NULL;
		headtwo = getAnglesList(rad, headtwo);
		fprintf(stderr, "radius %d, num angles %d\n", rad, list_length(headtwo));
		//if (rad < 3) print_list(headtwo);
		delete_list(headtwo);
	}
	fprintf(stderr, "Finish test radii\n");*/
	/* End simple test loop */	

	/* Parse tuples separately since args will differ between C fcns */
	int radius;
	PyArrayObject *radonone, *radontwo;
	//fprintf(stderr, "Start variable read\n");
	if (!PyArg_ParseTuple(args, "OOi", &radonone, &radontwo, &radius))
		return NULL;
	if (radonone == NULL) return NULL;
	if (radontwo == NULL) return NULL;

	/* Create list of angles to check, number of angles is based on radius */
	struct item *head = NULL;
	head = getAnglesList(radius, head);
	int numangles = list_length(head);
	//fprintf(stderr, "Finish get angles, radius %d, num angles %d\n", radius, list_length(head));

	/* dimensions error checking */
	if (radonone->dimensions[0] != radontwo->dimensions[0] 
		|| radonone->dimensions[1] != radontwo->dimensions[1]) {
		fprintf(stderr, "\n%s: Radon arrays are of different dimensions (%d,%d) vs. (%d,%d)\n\n",
			__FILE__,
			radonone->dimensions[0], radonone->dimensions[1],
			radontwo->dimensions[0], radontwo->dimensions[1]);
		return NULL;
	}

	/* Get the dimensions of the input */
	int numrows = radonone->dimensions[0];
	int numcols = radonone->dimensions[1];
	//fprintf(stderr, "Dimensions: %d rows by %d cols\n", numrows, numcols);
	if (2*radius > numcols) {
		fprintf(stderr, "\n%s: Shift diameter %d is larger than Radon array dimensions (%d,%d))\n\n",
			__FILE__, radius*2,
			radontwo->dimensions[0], radontwo->dimensions[1]);
		return NULL;
	}

	/*
	double test;
	test = *((double *)PyArray_GETPTR2(radonone, 0, 0));
	fprintf(stderr, "Array 1 test value at (0,0) = %.3f\n", test);
	test = *((double *)PyArray_GETPTR2(radontwo, 0, 0));
	fprintf(stderr, "Array 2 test value at (0,0) = %.3f\n", test);
	*/

	/* Determine the dimensions for the output */
	npy_intp outdims[2] = {numrows, numangles};

	/* Make a new double matrix of desired dimensions */
	//fprintf(stderr, "Creating output array of dimensions %d and %d\n", numrows, numangles);
	import_array(); // this is required to use PyArray_New() and PyArray_SimpleNew()
	PyArrayObject *output;
	//output = (PyArrayObject *) PyArray_New(&PyArray_Type, 2, outdims, NPY_DOUBLE, NULL, NULL, 0, 0, NULL);
	output = (PyArrayObject *) PyArray_SimpleNew(2, outdims, NPY_DOUBLE);
	//fprintf(stderr, "Finish create output array\n");

	/* Do the calculation. */

	int row;
	#pragma omp parallel for
	for (row=0; row<numrows; row++)  {
		struct item *current;
		int anglecol=0;
		for(current=head; current!=NULL; current=current->next) {
			/* calculation of cross correlation */
			double rawshift = radius*sin(current->angle);
			int shift;
			if (rawshift > 0) {
				shift = (int) (radius*sin(current->angle) + 0.5);
			} else {
				shift = (int) (radius*sin(current->angle) - 0.5);
			}
			//fprintf(stderr, "raw = %.3f; shift = %d\n", rawshift, shift);
			int i,j,ishift,jshift;
			double onevalue, twovalue;
			double outputsum = 0.0;
			//fprintf(stderr, "Position %d, %d\n", row, anglecol);
			for (i=0; i<numrows; i++)  {
				for (j=0; j<numcols; j++)  {
					ishift = i+row;
					if (ishift >= numrows) ishift -= numrows; // wrap overflow values
					if (ishift < 0) ishift += numrows; // wrap negative values
					jshift = j+shift;
					if (jshift >= numcols) jshift -= numcols; // wrap overflow values
					if (jshift < 0) jshift += numcols; // wrap negative values
					//fprintf(stderr, "%d, %d <-", ishift, jshift);
					onevalue = *((double *)PyArray_GETPTR2(radonone, ishift, jshift));
					//fprintf(stderr, "-> %d, %d\n", i, j);
					twovalue = *((double *)PyArray_GETPTR2(radontwo, i, j));
					outputsum += onevalue * twovalue;
			}}
			outputsum /= (numrows*numcols);
			*(double *) PyArray_GETPTR2(output, row, anglecol) = outputsum;
			/* interation variables */
			anglecol++;
	}  }

	/* clean up any memory leaks */
	delete_list(head);

	return PyArray_Return(output);
}
