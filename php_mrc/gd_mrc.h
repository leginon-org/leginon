/*
  +----------------------------------------------------------------------+
  | PHP Extension to read MRC file format as a gd image resource         |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

/* gd image resource */
static int le_gd; 

/* insert mrc data into an image resource pixel array */
void mrc_to_image(MRC *mrc, int ** tpixels, int pmin, int pmax, int binning, int skip, int kernel, float sigma, int colormap);

void mrc_to_image(MRC *mrc, int ** tpixels, int pmin, int pmax, int binning, int skip, int kernel, float sigma, int colormap);
void mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars);
void mrc_to_float(MRC *mrc, float *pdata_array);

/* return pixel indexes to average for binning */
int getIndexes(int *indexes, int binning, int index, int imagewidth);
int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth); 

int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC);
int gdreadMRCData(gdIOCtx *io_ctx, MRC *pMRC);
int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC);

