#ifndef POINT_H
#define POINT_H

#include "imgbase.h"

/* Data Structures for Points */
typedef struct point_type {
    int dim;             /* dim must be less than 5 */
    double  x[4];         
    BOOLEAN flag;       /* generic flag - to be used for whatever. */
    double weight1;
    double weight2;
    struct point_type   *next;
} POINT;

typedef struct point_list_type {
    POINT   *head;
    POINT   *tail;
    int     num_elements;   /* number of elements in linked list. */
    double  area;           /* area formed by the linked list of points. */
    struct  point_list_type *next;
} POINT_LIST;

typedef struct list_of_point_list_type {
    POINT_LIST   *head;
    POINT_LIST   *tail;
    int     num_elements;   /* number of lists in linked list. */
    struct  list_of_point_list_type *next;
} LIST_OF_POINT_LIST;


typedef struct point_line_type {
    int num_points;   /* number of elements in linked list. */
    int *x;
    int *y;
    double orient;
    struct  point_line_type *next;
} POINT_LINE;

typedef struct list_of_point_line_type {
    POINT_LINE   *head;
    POINT_LINE   *tail;
    int     num_lines;   /* number of lines in the linked list. */
    struct  list_of_point_line_type *next;
} LIST_OF_POINT_LINE;


/* Function Prototypes  for Points */
POINT       *alloc_point(int dim);

void        free_point(POINT *p);

POINT_LIST  *alloc_point_list(void);

POINT       *copy_point(POINT *p);

void        write_point_to_a_file(FILE *out_file, POINT *p);

POINT       *read_point_from_file(FILE *in_file);

POINT_LIST * push_into_list_of_point(POINT_LIST *point_list, POINT *p);

POINT      * pop_from_list_of_point(POINT_LIST *point_list);

POINT_LIST * put_in_linked_list_of_point(POINT_LIST *point_list, POINT *p);

POINT_LIST * delete_from_linked_list_of_point(POINT_LIST *point_list, POINT *p);

void        free_linked_list_of_point(POINT_LIST *point_list);

int         is_weight_in_point_list (POINT_LIST *p, double w);

void print_list_of_point (POINT_LIST *pt_list);

POINT_LIST * read_list_of_point(char * filename);

POINT_LIST * point_list_cc_to_ccc(POINT_LIST *pt_list);

int sizeof_point_list( POINT_LIST *point_list);

void add_point_list( POINT_LIST *poing_list, void * dest);

POINT_LIST * extract_point_list(void * dest);


/* Function Prototypes  for List of Point lists */
LIST_OF_POINT_LIST * alloc_list_of_point_list(void);

LIST_OF_POINT_LIST * put_in_list_of_point_list(LIST_OF_POINT_LIST *list_of_point_list, POINT_LIST *p_list);

LIST_OF_POINT_LIST * delete_from_list_of_point_list(LIST_OF_POINT_LIST *lp_list, POINT_LIST *p);

void free_list_of_point_list(LIST_OF_POINT_LIST *list_of_point_list);

int sizeof_list_of_point_list( LIST_OF_POINT_LIST *lp_list);

void add_list_of_point_list( LIST_OF_POINT_LIST *lp_list, void * dest);

LIST_OF_POINT_LIST * extract_list_of_point_list(void * dest);

void prune_point_lists(LIST_OF_POINT_LIST *lp_list, int method, float threshold);

int write_list_of_point_lists(LIST_OF_POINT_LIST *lp_list, char *outfilename);

LIST_OF_POINT_LIST * read_list_of_point_lists(char *infilename);


/* Function Prototypes for Point Lines */
POINT_LINE * alloc_point_line(int num);

void free_point_line(POINT_LINE *p);

LIST_OF_POINT_LINE * alloc_list_of_point_line(void);

LIST_OF_POINT_LINE * put_in_list_of_point_line(LIST_OF_POINT_LINE *list_of_point_line, POINT_LINE *p_line);

void free_list_of_point_line(LIST_OF_POINT_LINE *list_of_point_line);
 
LIST_OF_POINT_LINE * extract_list_of_point_lines(void *dest);

void add_list_of_point_lines(LIST_OF_POINT_LINE *l_lines, void *dest);

int fit_circle_to_point_list(POINT_LIST *plist, double *cx, double *cy, double *r, double W);
   
#endif /* POINT_H */ 
