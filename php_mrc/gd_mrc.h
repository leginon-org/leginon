/*
  +----------------------------------------------------------------------+
  | PHP Extension to read MRC file format as a gd image resource         |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/


/* insert mrc data into an image resource pixel array */
void mrc_to_image(MRC *mrc, int ** tpixels, int pmin, int pmax, int binning, int skip, int kernel, float sigma, int colormap);

/* return pixel indexes to average for binning */
void getIndexes(int indexes[], int binning, int index, int imagewidth);
void getMaskDataIndexes(int indexes[], int masksize, int index, int imagewidth);

/* gd image resource */
static int le_gd; 
