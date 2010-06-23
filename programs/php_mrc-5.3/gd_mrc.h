/*
  +----------------------------------------------------------------------+
  | PHP Extension to read MRC file format as a gd image resource         |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

/* gd image resource */
static int le_gd; 

void mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars);
void mrc_to_frequence(MRC *mrc, int *frequency);
void mrc_to_float(MRC *mrc, float *pdata_array);

/* return pixel indexes to average for binning */
int getIndexes(int *indexes, int binning, int index, int imagewidth);
int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth); 

int gdreadMRCHeader(gdIOCtx *io_ctx, MRCHeader *pMRCHeader);
int gdloadMRC(gdIOCtx *io_ctx, int in_length, MRC *pMRC);

void mrc_copy(MRCPtr pmrc_dst, MRCPtr pmrc_src, int x1, int y1, int x2, int y2) ;
void mrc_copy_to(MRCPtr pmrc_dst, MRCPtr pmrc_src, int dstX, int dstY, int srcX, int srcY, int srcW, int srcH);
int mrc_copy_from_file(MRCPtr pmrc_dst, char *pszFilename, int dstX, int dstY, int srcX, int srcY);
MRCPtr mrc_create(int x_size, int y_size);
MRCPtr mrc_rotate(MRC *mrc_src, double angle, int resize);
void mrc_destroy(MRCPtr pmrc);
void mrc_to_gd(MRC *mrc, gdImagePtr im, int pmin, int pmax);
void mrc_log(MRC *mrc);
void mrc_binning(MRC *mrc, int binning, int skip_avg);
void mrc_filter(MRC *mrc, int binning, int kernel, float sigma);
void mrc_convert_to_float(MRC *mrc_src, MRC *mrc_dst);
int rotate_2d_image (float *in_img, float *out_img, int h, int w, double ang, int new_h, int new_w, float default_value);
float linear_2d_interp (float *in_img, int h, int w, float old_x, float old_y, float default_value);
float linear_interp(float low_value, float high_value, float position);
void cal_rotated_image_dimension(int h, int w, double ang, int *new_h, int *new_w);
