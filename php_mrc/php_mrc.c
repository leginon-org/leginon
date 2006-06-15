/*
  +----------------------------------------------------------------------+
  | PHP MRC Extension                                                    |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+

  $Id: php_mrc.c,v 1.18 2006-06-15 21:13:54 dfellman Exp $ 
*/

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "php.h"
#include "php_ini.h"
#include "ext/standard/info.h"
#include "gd.h"
#include "mrc.h"
#include "gd_mrc.h"
#include "filter.h"
#ifdef HAVE_FFTW
#include "fft.h"
#endif
#include "php_mrc.h"

/* If you declare any globals in php_mrc.h uncomment this:
ZEND_DECLARE_MODULE_GLOBALS(mrc)
*/

/* True global resources - no need for thread safety here */
static int le_mrc;

/* mrc_functions[]
 *
 * Every user visible function must have an entry in mrc_functions[].
 */
function_entry mrc_functions[] = {
	ZEND_FE(gdimageinfo, NULL)
	ZEND_FE(imagegaussianfilter, NULL)
	ZEND_FE(imagelogscale, NULL)
	ZEND_FE(imagehistogram, NULL)
#ifdef HAVE_FFTW
	ZEND_FE(imagefftw, NULL)
	ZEND_FE(mrcfftw, NULL)
#endif
	ZEND_FE(mrcinfo, NULL)
	ZEND_FE(mrcgetinfo, NULL)
	ZEND_FE(mrcsx, NULL)
	ZEND_FE(mrcsy, NULL)
	ZEND_FE(mrcread, NULL)
	ZEND_FE(mrcreadfromstring, NULL)
	ZEND_FE(mrccreate, NULL)
	ZEND_FE(mrcwrite, NULL)
	ZEND_FE(mrctoimage, NULL)
	ZEND_FE(mrccopy, NULL)
	ZEND_FE(mrcbinning, NULL)
	ZEND_FE(mrcgaussianfilter, NULL)
	ZEND_FE(mrclogscale, NULL)
	ZEND_FE(mrcgetdata, NULL)
	ZEND_FE(mrcgetscale, NULL)
	ZEND_FE(mrcputdata, NULL)
	ZEND_FE(mrcrotate, NULL)
	ZEND_FE(mrcupdateheader, NULL)
	ZEND_FE(mrchistogram, NULL)
	ZEND_FE(mrcdestroy, NULL)
	{NULL, NULL, NULL}	/* Must be the last line in mrc_functions[] */
};


/* mrc_module_entry
 */
zend_module_entry mrc_module_entry = {
#if ZEND_MODULE_API_NO >= 20010901
	STANDARD_MODULE_HEADER,
#endif
	"mrc",
	mrc_functions,
	PHP_MINIT(mrc),
	PHP_MSHUTDOWN(mrc),
	PHP_RINIT(mrc),		/* Replace with NULL if there's nothing to do at request start */
	PHP_RSHUTDOWN(mrc),	/* Replace with NULL if there's nothing to do at request end */
	PHP_MINFO(mrc),
#if ZEND_MODULE_API_NO >= 20010901
	"1.2", /* Replace with version number for your extension */
#endif
	STANDARD_MODULE_PROPERTIES
};


#ifdef COMPILE_DL_MRC
ZEND_GET_MODULE(mrc)
#endif

/* PHP_INI
 */
/* Remove comments and fill if you need to have entries in php.ini
PHP_INI_BEGIN()
    STD_PHP_INI_ENTRY("mrc.global_value",      "42", PHP_INI_ALL, OnUpdateInt, global_value, zend_mrc_globals, mrc_globals)
    STD_PHP_INI_ENTRY("mrc.global_string", "foobar", PHP_INI_ALL, OnUpdateString, global_string, zend_mrc_globals, mrc_globals)
PHP_INI_END()
*/


/* php_mrc_init_globals
 */
/* Uncomment this function if you have INI entries
static void php_mrc_init_globals(zend_mrc_globals *mrc_globals)
{
	mrc_globals->global_value = 0;
	mrc_globals->global_string = NULL;
}
*/


/* php_free_mrc
 */
static void php_free_mrc(zend_rsrc_list_entry *rsrc TSRMLS_DC)
{
	mrc_destroy((MRCPtr)rsrc->ptr);
}



/* PHP_MINIT_FUNCTION
 */
PHP_MINIT_FUNCTION(mrc)
{
	le_gd = zend_fetch_list_dtor_id("gd"); 
	le_mrc = zend_register_list_destructors_ex(php_free_mrc, NULL, "mrc", module_number);
	/* If you have INI entries, uncomment these lines 
	ZEND_INIT_MODULE_GLOBALS(mrc, php_mrc_init_globals, NULL);
	REGISTER_INI_ENTRIES();
	*/
	return SUCCESS;
}


/* PHP_MSHUTDOWN_FUNCTION
 */
PHP_MSHUTDOWN_FUNCTION(mrc)
{
	/* uncomment this line if you have INI entries
	UNREGISTER_INI_ENTRIES();
	*/
	return SUCCESS;
}


/* Remove if there's nothing to do at request start */
/* PHP_RINIT_FUNCTION
 */
PHP_RINIT_FUNCTION(mrc)
{
	return SUCCESS;
}


/* Remove if there's nothing to do at request end */
/* PHP_RSHUTDOWN_FUNCTION
 */
PHP_RSHUTDOWN_FUNCTION(mrc)
{
	return SUCCESS;
}


/* PHP_MINFO_FUNCTION
 */
PHP_MINFO_FUNCTION(mrc)
{
	php_info_print_table_start();
	php_info_print_table_header(2, "mrc support", "enabled");
#if HAVE_FFTW
	php_info_print_table_row(2, "FFTW support", "enabled");
#else
	php_info_print_table_row(2, "FFTW support", "no");
#endif
	php_info_print_table_end();

	/* Remove comments if you have entries in php.ini
	DISPLAY_INI_ENTRIES();
	*/
}


/**
 * get image information
 *
 * Description:
 * array imagegaussianfilter ( resource image )
 **/
ZEND_FUNCTION(gdimageinfo)
{
	zval **imgind;
	char	*key;
	gdImagePtr im;
	int argc = ZEND_NUM_ARGS();

	if (argc != 1 ) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &imgind);

	ZEND_FETCH_RESOURCE(im, gdImagePtr, imgind, -1, "Image", le_gd);

	array_init(return_value);
	key = "sx";
	add_assoc_long(return_value, key, im->sx);
	key = "sy";
	add_assoc_long(return_value, key, im->sy);
	key = "colorsTotal";
	add_assoc_long(return_value, key, im->colorsTotal);
	key = "red[gdMaxColors]";
	key = "green[gdMaxColors]";
	key = "blue[gdMaxColors]";
	key = "open[gdMaxColors]";
	key = "transparent";
	add_assoc_long(return_value, key, im->transparent);
	key = "polyAllocated";
	add_assoc_long(return_value, key, im->polyAllocated);
	key = "styleLength";
	add_assoc_long(return_value, key, im->styleLength);
	key = "stylePos";
	add_assoc_long(return_value, key, im->stylePos);
	key = "interlace";
	add_assoc_long(return_value, key, im->interlace);
	key = "thick";
	add_assoc_long(return_value, key, im->thick);
	key = "trueColor";
	add_assoc_long(return_value, key, im->trueColor);
	key = "alphaBlendingFlag";
	add_assoc_long(return_value, key, im->alphaBlendingFlag);
	key = "saveAlphaFlag";
	add_assoc_long(return_value, key, im->saveAlphaFlag);
}

/**
 * apply gaussian filter to an image
 *
 * Description:
 * int imagegaussianfilter ( resource image [, int kernel [, float sigma ]])
 **/
ZEND_FUNCTION(imagegaussianfilter)
{
	zval **imgind, **KERNEL, **SIGMA;
	gdImagePtr im;
	int argc = ZEND_NUM_ARGS();
	int	kernel;
	float	sigma = 1.0;

	if (argc < 3 ) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &imgind, &KERNEL, &SIGMA);

	convert_to_long_ex(KERNEL);
	convert_to_double_ex(SIGMA);
	kernel = Z_LVAL_PP(KERNEL);
	if (sigma > 1)
		sigma = Z_DVAL_PP(SIGMA);


	if (sigma == 0) 
		zend_error(E_ERROR, "%s(): sigma cannot be 0", get_active_function_name(TSRMLS_C));

	if (kernel % 2 != 1)
		zend_error(E_ERROR, "%s(): kernel must be an odd number", get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(im, gdImagePtr, imgind, -1, "Image", le_gd);

	filtergaussian(im, kernel, sigma);

	RETURN_TRUE;
}


/**
 * scale an image with log
 *
 * Description:
 * bool imagelogscale ( resource image )
 */
ZEND_FUNCTION(imagelogscale)
{
	zval **imgind;
	gdImagePtr im_src;
	int argc = ZEND_NUM_ARGS();

	if (argc != 1 ) 
	{
		WRONG_PARAM_COUNT;
	} 
	zend_get_parameters_ex(argc, &imgind);

	ZEND_FETCH_RESOURCE(im_src, gdImagePtr, imgind, -1, "Image", le_gd);

	gdLogScale(im_src);
	RETURN_TRUE;
}


/** imagehistogram(resource image) */
ZEND_FUNCTION(imagehistogram)
{
        zval **imgind, **NBBARS;
        gdImagePtr im_src;
        int argc = ZEND_NUM_ARGS();
        int i, i1, i2, j, ij, M, N, pixel, interval, nb, nb_bars=50;
        unsigned char *data_array;
        unsigned char data, fmin=0, fmax=0;

        if (argc > 2 )
        {
                WRONG_PARAM_COUNT;
        }
        zend_get_parameters_ex(argc, &imgind, &NBBARS);

        if (argc == 2)
        {
                convert_to_long_ex(NBBARS);
                if (Z_LVAL_PP(NBBARS))
                        nb_bars = Z_LVAL_PP(NBBARS);
        }

        ZEND_FETCH_RESOURCE(im_src, gdImagePtr, imgind, -1, "Image", le_gd);

        if (im_src) {
                array_init(return_value);
                M = im_src->sx;
                N = im_src->sy;
                data_array = malloc(sizeof(unsigned char)*M*N);
                for (i = 0; i < M; i++) {
                        for (j = 0; j < N; j++) {
                                ij = i*N + j;
                                pixel = gdImageGetPixel(im_src,i,j);
                                // Y = 0.3RED + 0.59GREEN +0.11Blue
                                data = (unsigned char)(.3*(pixel & 0xff) + .59*((pixel >> 8) & 0xff) + .11*((pixel >> 16) & 0xff));
                                data_array[ij] = data;
                                fmax = MAX(fmax, data_array[ij]);
                                fmin = MIN(fmin, data_array[ij]);
                        }
                }
                interval=(fmax-fmin)/nb_bars;

                for (i=0; i<nb_bars; i++) {
                        nb=0;
                        for (j=0; j<M*N; j++) {
                                i1 = fmin+(i-1)*interval;
                                i2 = fmin+i*interval;
                                if (data_array[j] > i1 && data_array[j] <=i2)
                                        nb++;
                        }
                        add_index_long(return_value, (fmin + i*interval), nb);
                }
                free(data_array);
        } else {
                RETURN_FALSE;
        }
}


#ifdef HAVE_FFTW

/**
 * generate FFT from a existing image resource.
 *
 * Description:
 * bool imagefftw ( resource image )
 */
ZEND_FUNCTION(imagefftw)
{
	zval **imgind, **MASK;
	gdImagePtr im_src;
	int argc = ZEND_NUM_ARGS();
	int mask=0;

	if (argc > 2 ) 
	{
		WRONG_PARAM_COUNT;
	} 
	zend_get_parameters_ex(argc, &imgind, &MASK);

	if (argc == 2)
	{
		convert_to_long_ex(MASK);
		mask = Z_LVAL_PP(MASK);
	}

	ZEND_FETCH_RESOURCE(im_src, gdImagePtr, imgind, -1, "Image", le_gd);

	gd_fftw(im_src, mask);
	RETURN_TRUE;
}


/**
 * compute discrete Fourier transform
 *
 * Description:
 * mrcfftw(resource src_mrc, int mask)
 * \htmlinclude mrcfft.html
 */
ZEND_FUNCTION(mrcfftw)
{

	zval	**data, **MASK;
	MRC	*pmrc;
	MRCPtr pmrc_dst;
	int	argc = ZEND_NUM_ARGS();
	int	mask = 0;
	int M, N;

	if (argc > 2 ) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &MASK);

	if (argc == 2)
	{
		convert_to_long_ex(MASK);
		mask = Z_LVAL_PP(MASK);
	}

	if (mask < 0) 
		zend_error(E_ERROR, "%s(): mask must be greater than 0", get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, data, -1, "MRCdata", le_mrc);
	mrc_fftw(pmrc, mask);

}


#endif

/**
 * retrieve MRC header information MRC file, URL or a String, as a PHP associative array.
 *
 * Description: array mrcinfo(string filename)
 */
ZEND_FUNCTION(mrcinfo)
{
	zval **data;
	MRCPtr pmrc;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &data) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_header_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, &(pmrc->header));
	_mrc_header_data(INTERNAL_FUNCTION_PARAM_PASSTHRU, pmrc);
	mrc_destroy(pmrc);

}

/**
 * retrieve header information from MRC resource, as a PHP associative array.
 *
 * Description: 
 * array mrcgetinfo(resource src_mrc) 
 */
ZEND_FUNCTION(mrcgetinfo)
{
	zval **MRCD;
	MRCPtr pmrc;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);
	_mrc_header_data(INTERNAL_FUNCTION_PARAM_PASSTHRU, pmrc);

}

/** 
 * Get image width
 *
 * Description:
 * int mrcsx(resource src_mrc)
 */
ZEND_FUNCTION(mrcsx)
{
	zval **MRCD;
	MRCPtr pmrc;
	int val;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);
	val = pmrc->header.nx;
	RETURN_LONG(val);

}


/** 
 * Get image height
 *
 * Description:
 * int mrcsy(resource src_mrc)
 */
ZEND_FUNCTION(mrcsy)
{
	zval **MRCD;
	MRCPtr pmrc;
	int val;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);
	val = pmrc->header.ny;
	RETURN_LONG(val);

}


/** 
 * read a MRC file
 *
 * Description:
 * resource mrcread(string filename)
 */
ZEND_FUNCTION(mrcread)
{

	zval **data;
	MRC *pmrc;
	int argc = ZEND_NUM_ARGS();

	if (argc != 1)
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data);

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);
	ZEND_REGISTER_RESOURCE(return_value, pmrc, le_mrc);

}


/** 
 * Create mrc resource from the data stream in the string
 *
 * Description:
 * resource mrcreadfromstring(string data)
 */
ZEND_FUNCTION(mrcreadfromstring)
{

	zval **data;
	MRC *pmrc;
	int argc = ZEND_NUM_ARGS();

	if (argc != 1)
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data);

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from_string(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);

	ZEND_REGISTER_RESOURCE(return_value, pmrc, le_mrc);

}


/** 
 * Create a new mrc image
 *
 * Description:
 * resource createmrc(int x_size, int y_size)
 */
ZEND_FUNCTION(mrccreate)
{
	zval **x_size, **y_size;
	MRCPtr pmrc;

	if (ZEND_NUM_ARGS() != 2 || zend_get_parameters_ex(2, &x_size, &y_size) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}

	convert_to_long_ex(x_size);
	convert_to_long_ex(y_size);


	pmrc = (MRCPtr)mrc_create(Z_LVAL_PP(x_size), Z_LVAL_PP(y_size));
	ZEND_REGISTER_RESOURCE(return_value, pmrc, le_mrc);
}


/** 
 * write MRC resource to file
 *
 * Description: bool mrcwrite(resource src_mrc, string filename) 
 *  \htmlinclude mrcwrite.html
 */
ZEND_FUNCTION(mrcwrite)
{
	zval	**MRCD, **file;
	MRCPtr	pmrc;
	char *fn = NULL;
	FILE *fp;
	int argc = ZEND_NUM_ARGS();
	int q = -1, i;

	if (argc < 1 || argc > 2 || zend_get_parameters_ex(argc, &MRCD, &file) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

	convert_to_string_ex(file);
	fn = Z_STRVAL_PP(file);
	if (!fn || fn == empty_string || php_check_open_basedir(fn TSRMLS_CC)) {
		php_error_docref(NULL TSRMLS_CC, E_WARNING, "Invalid filename '%s'", fn);
		RETURN_FALSE;
	}

	fp = VCWD_FOPEN(fn, "wb");
	if (!fp) {
		php_error_docref(NULL TSRMLS_CC, E_WARNING, "Unable to open '%s' for writing", fn);
		RETURN_FALSE;
	}
	
	int uElements = writeMRC(fp, pmrc);

	fflush(fp);
	fclose(fp);
	RETURN_TRUE;
}


/** convert a mrc resource to an image resource
 *
 * Description:
 * resource mrctoimage(resource src_mrc [, int pix_min [, int pix_max [, int color_map ]]])
 */ 
ZEND_FUNCTION(mrctoimage)
{
	char	*key;
	zval	**MRCD, **PMIN, **PMAX, **COLOR_MAP;
	MRCPtr	pmrc;
	gdImagePtr im;
	float	*data_array;
	int	minPix = densityMIN,
		maxPix = -1,
		argc = ZEND_NUM_ARGS();


	int nWidth = 0;
	int nHeight = 0;
	int colormap = 0;

	if (argc < 1 || argc > 4) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &MRCD, &PMIN, &PMAX, &COLOR_MAP);

	if (argc>1) {
		convert_to_long_ex(PMIN);
		minPix = Z_LVAL_PP(PMIN);
	}
	if (argc>2) {
		convert_to_long_ex(PMAX);
		maxPix = Z_LVAL_PP(PMAX);
	}
	if (argc>3) {
		convert_to_long_ex(COLOR_MAP);
		colormap = Z_LVAL_PP(COLOR_MAP);
	}

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);
	if (minPix<0)
		minPix = densityMIN;

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
	nWidth = pmrc->header.nx;
	nHeight = pmrc->header.ny;
		
	im = gdImageCreateTrueColor(nWidth, nHeight);
	gdImageColorAllocate(im, 0, 0, 0);

	mrc_to_gd(pmrc, im, minPix, maxPix, colormap);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}


/** 
 * Copy part of an mrc
 *
 * mrccopy(int dst_mrc, int src_mrc, int dst_x, int dst_y, int src_x, int src_y, int src_w, int src_h)
 */ 
ZEND_FUNCTION(mrccopy)
{
	zval **SMRC, **DMRC, **SX, **SY, **SW, **SH, **DX, **DY;
	MRCPtr mrc_dst, mrc_src;
	int srcH, srcW, srcY, srcX, dstY, dstX;

	if (ZEND_NUM_ARGS() != 8 ||	
		zend_get_parameters_ex(8, &DMRC, &SMRC, &DX, &DY, &SX, &SY, &SW, &SH) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}

	ZEND_FETCH_RESOURCE(mrc_src, MRCPtr, SMRC, -1, "MRCdata", le_mrc);
	ZEND_FETCH_RESOURCE(mrc_dst, MRCPtr, DMRC, -1, "MRCdata", le_mrc);

	convert_to_long_ex(SX);
	convert_to_long_ex(SY);
	convert_to_long_ex(SW);
	convert_to_long_ex(SH);
	convert_to_long_ex(DX);
	convert_to_long_ex(DY);

	srcX = Z_LVAL_PP(SX);
	srcY = Z_LVAL_PP(SY);
	srcH = Z_LVAL_PP(SH);
	srcW = Z_LVAL_PP(SW);
	dstX = Z_LVAL_PP(DX);
	dstY = Z_LVAL_PP(DY);

	mrc_copy_to(mrc_dst, mrc_src, dstX, dstY, srcX, srcY, srcW, srcH);
	RETURN_TRUE;
}


/** 
 * bin a mrc image
 *
 * Description:
 * bool mrcbinning(resource src_mrc, int binning [, bool skip_avg]) 
 */
ZEND_FUNCTION(mrcbinning)
{

	zval **data, **BINNING, **SKIP_AVG;
	MRCPtr pmrc;
	int argc = ZEND_NUM_ARGS();
	int binning = 1;
	int skip_avg = 0;

	if (argc < 1 || argc > 3) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &BINNING, &SKIP_AVG);

	if (argc>1) {
		convert_to_long_ex(BINNING);
		binning = Z_LVAL_PP(BINNING);
	}
	if (argc>2) {
		convert_to_boolean_ex(SKIP_AVG);
		skip_avg = Z_LVAL_PP(SKIP_AVG);
	}

	if (binning <= 0) 
		zend_error(E_ERROR, "%s(): binning must be greater than 0", get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, data, -1, "MRCdata", le_mrc);
	mrc_binning(pmrc, binning, skip_avg);
	RETURN_TRUE;

}


/** 
 * apply a gaussion filter
 *
 * Description:
 * bool mrcgaussianfilter(resource src_mrc, int binning, int kernel, float sigma)
 */
ZEND_FUNCTION(mrcgaussianfilter)
{

	zval	**data, **BINNING, **KERNEL, **SIGMA;
	MRCPtr	pmrc;
	int	argc = ZEND_NUM_ARGS();
	int	kernel= 1;
	int	binning= 1;
	float	sigma = 1.0;

	if (argc != 4) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &BINNING, &KERNEL, &SIGMA);

	convert_to_long_ex(BINNING);
	convert_to_long_ex(KERNEL);
	convert_to_double_ex(SIGMA);
	kernel = Z_LVAL_PP(KERNEL);
	binning = Z_LVAL_PP(BINNING);
	sigma = Z_DVAL_PP(SIGMA);

	if (sigma == 0) 
		zend_error(E_ERROR, "%s(): sigma cannot be 0", get_active_function_name(TSRMLS_C));

	if (kernel % 2 != 1)
		zend_error(E_ERROR, "%s(): kernel must be an odd number", get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, data, -1, "MRCdata", le_mrc);

	mrc_filter(pmrc, binning, kernel, sigma);
	RETURN_TRUE;

}


/**
 * apply a log scale  
 * 
 * Description:
 * bool mrclogscale(resource src_mrc) 
 */
ZEND_FUNCTION(mrclogscale)
{

	zval **data;
	MRCPtr pmrc;
	int argc = ZEND_NUM_ARGS();

	if (argc !=  1)
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data);

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, data, -1, "MRCdata", le_mrc);
	mrc_log(pmrc);
	RETURN_TRUE;

}


/**
 * retrieve mrc data 
 * 
 * Description:
 * array mrcgetdata(resource src_mrc) 
 */
ZEND_FUNCTION(mrcgetdata)
{
	char	*key;
	zval	**MRCD;
	MRCPtr	pmrc;
	MRCHeader	mrch;
		float	*data_array;

		int	i,n;


	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

	mrch = pmrc->header;
	data_array = (float *)pmrc->pbyData;
	n = mrch.nx * mrch.ny;
	array_init(return_value);
	for (i=0; i<n; i++) {
		add_next_index_double(return_value, data_array[i]);
	}
}


/**
 * get min and max value scaled within +/- 3 stddev
 *
 * Description:
 * array mrcgetscale(resource src_mrc, int density_max)
 */ 
ZEND_FUNCTION(mrcgetscale)
{
		char	*key;
		zval	**MRCD, **DENSITY_MAX;
		MRCPtr	pmrc;
		MRCHeader	mrch;

		int argc = ZEND_NUM_ARGS();
		int densitymax;
		
		float pmin, pmax, pmean, rms, scale;
		float smin, smax;


		if (argc != 2 || zend_get_parameters_ex(argc, &MRCD, &DENSITY_MAX) == FAILURE) {
			ZEND_WRONG_PARAM_COUNT();
		}

		convert_to_long_ex(DENSITY_MAX);
		densitymax = Z_LVAL_PP(DENSITY_MAX);

		ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

		mrch = pmrc->header;
		pmean = mrch.amean;
		pmin = mrch.amin;
		pmax = mrch.amax;
		pmean = mrch.amean;
		rms	= mrch.rms;
		if (!rms || !pmean)
			mrc_update_header(pmrc);

		scale = pmax - pmin;

		if (scale!=0) {
			smin = (pmean-3*rms)*densitymax/scale;
			smax = (pmean+3*rms)*densitymax/scale;
		}
		

		array_init(return_value);
		add_next_index_double(return_value, smin);
		add_next_index_double(return_value, smax);
		key = "smin";
		add_assoc_double(return_value, key, smin);
		key = "smax";
		add_assoc_double(return_value, key, smax);

}


/** 
 * put data
 *
 * Description:
 * mrcputdata(resource src_mrc, array data)
 */ 
ZEND_FUNCTION(mrcputdata)
{
	zval	**MRCD, **input , **entry;
	MRCPtr	pmrc;
	MRCHeader	mrch;
	HashPosition pos;
	

	float	*data_array;
	float val;

	int i, argc = ZEND_NUM_ARGS();

	if (argc != 2 || zend_get_parameters_ex(argc, &MRCD, &input) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}


	if (Z_TYPE_PP(input) != IS_ARRAY) {
				zend_error(E_ERROR, "%s(): Input is not a MRC string ",
								 get_active_function_name(TSRMLS_C));
	}

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

	data_array = (float *)pmrc->pbyData;

	/* Go through array array and add values to the return array */
	i=0;
	zend_hash_internal_pointer_reset_ex(Z_ARRVAL_PP(input), &pos);
	while (zend_hash_get_current_data_ex(Z_ARRVAL_PP(input), (void **)&entry, &pos) == SUCCESS) {

		
		(*entry)->refcount++;
		switch (Z_TYPE_PP(entry)) {
			case IS_DOUBLE:
				val = Z_DVAL_PP(entry);
				break;
			case IS_LONG:
				val = Z_LVAL_PP(entry);
				break;
			default:
				val = 0;
		}
		data_array[i] =  val;

		zend_hash_move_forward_ex(Z_ARRVAL_PP(input), &pos);
		i++;
	}
}


/** 
 * Rotate an image with a given angle
 *
 * Description:
 * mrcrotate(resource src_mrc, float angle [, boolean resize ])
 */ 
ZEND_FUNCTION(mrcrotate)
{
	zval	**MRCD, **ANGLE, **RESIZE;
	MRCPtr	pmrc, pmrc_rotated;
	int argc = ZEND_NUM_ARGS();
	int resize = 0;
	double angle=0;


	if (argc < 1 || argc > 3) 
	{
		ZEND_WRONG_PARAM_COUNT();
	} 

	zend_get_parameters_ex(argc, &MRCD, &ANGLE, &RESIZE);

	convert_to_double_ex(ANGLE);
	angle = Z_DVAL_PP(ANGLE);

	if (argc>2) {
		convert_to_boolean_ex(RESIZE);
		resize = Z_LVAL_PP(RESIZE);
	}


	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);
	pmrc_rotated = (MRCPtr)mrc_rotate(pmrc, angle, resize);
	ZEND_REGISTER_RESOURCE(return_value, pmrc_rotated, le_mrc);

}


/**
 * update header information
 *
 * Description:
 * mrcupdateheader(resource src_mrc)
 */ 
ZEND_FUNCTION(mrcupdateheader)
{
	char	*key;
	zval	**MRCD;
	MRCPtr	pmrc;
		float	*data_array;

		int	i;
	float	f_val, fmin, fmax, fmean, stddev;
	double  somme, somme2, n;


	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);
	mrc_update_header(pmrc);

}


/**
 * retrieve classes and frequences from MRC file, URL
 *
 * Description:
 * array mrchistogram(string filename)
 */
ZEND_FUNCTION(mrchistogram)
{
	zval **data, **NBBARS;
	MRCPtr pmrc;
	int	argc = ZEND_NUM_ARGS();
	int	nb_bars=50;
	int	j;
	int	*frequency;
	float	*classes;

	if (argc > 2) {
		ZEND_WRONG_PARAM_COUNT();
	}

	zend_get_parameters_ex(argc , &data, &NBBARS);
	convert_to_string_ex(data);

	if (argc == 2)
	{
		convert_to_long_ex(NBBARS);
		nb_bars = Z_LVAL_PP(NBBARS);
	}

	frequency = malloc(sizeof(int)*nb_bars);
	classes = malloc(sizeof(float)*nb_bars);

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);

	mrc_to_histogram(pmrc, frequency, classes, nb_bars);

	array_init(return_value);
	for (j = 0; j < nb_bars; j++) {
		add_index_long(return_value, classes[j], frequency[j]);
	}

	free(frequency);
	free(classes);
	mrc_destroy(pmrc);
}


/**
 * destroy a mrc resource
 *
 * Description:
 * bool mrcdestroy(resource src_mrc)
 *
 * frees any memory associated with src_mrc
 */
ZEND_FUNCTION(mrcdestroy)
{
	zval **MRCD;
	MRCPtr pmrc;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

	zend_list_delete(Z_LVAL_PP(MRCD));

	RETURN_TRUE;
}

/**
 * static void _mrc_header_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc)
 */
static void _mrc_header_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRCHeader *pmrch) {
	char *ptfile;
	convert_to_string_ex(data);
	ptfile = (char *)((*data)->value.str.val);
	if(loadMRCHeader(ptfile, pmrch)==-1) {
				zend_error(E_ERROR, "%s(): %s : No such file or directory ", 
				get_active_function_name(TSRMLS_C),ptfile);
	}
}

/**
 * static void _mrc_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc)
 */
static void _mrc_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc) {

	MRC *pmrc_src;
	char *ptfile;

	convert_to_string_ex(data);
	pmrc_src = (MRC *) malloc (sizeof (MRC));
	ptfile = (char *)((*data)->value.str.val);
	if(loadMRC(ptfile, pmrc_src )==-1) {
				zend_error(E_ERROR, "%s(): %s : No such file or directory ", 
				get_active_function_name(TSRMLS_C),ptfile);
	}
	
	/**
	* copy mrc source as mrc float to further manipulation
	**/
	mrc_convert_to_float(pmrc_src, pmrc);
	mrc_destroy(pmrc_src);

}


/**
 * static void _mrc_image_create_from_string(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc)
 */
static void _mrc_image_create_from_string(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc) {
	gdIOCtx *io_ctx;
	MRC *pmrc_src;
	int in_length=0;

	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}

	pmrc_src = (MRC *) malloc (sizeof (MRC));
	in_length = (int)((*data)->value.str.len);
	if (gdloadMRC(io_ctx, in_length, pmrc_src)==-1) {
				zend_error(E_ERROR, "%s():  Input is not a MRC string ", 
				get_active_function_name(TSRMLS_C));
	}

	/**
	* copy mrc source as mrc float to further manipulation
	**/
	mrc_convert_to_float(pmrc_src, pmrc);
	mrc_destroy(pmrc_src);
	free(io_ctx);
	
}


/**
 *  static void _mrc_header_data(INTERNAL_FUNCTION_PARAMETERS,  MRC *pMRC)
 */
static void _mrc_header_data(INTERNAL_FUNCTION_PARAMETERS,  MRC *pMRC) {
	
	MRCHeader mrch;
	char *key;
	mrch = pMRC->header;

	array_init(return_value);
	key = "nx";
	add_assoc_long(return_value, key, mrch.nx);
	key = "ny";
	add_assoc_long(return_value, key, mrch.ny);
	key = "nz";
	add_assoc_long(return_value, key, mrch.nz);
	key = "mode";
	add_assoc_long(return_value, key, mrch.mode);
	key = "nxstart";
	add_assoc_long(return_value, key, mrch.nxstart);
	key = "nystart";
	add_assoc_long(return_value, key, mrch.nystart);
	key = "nzstart";
	add_assoc_long(return_value, key, mrch.nzstart);
	key = "mx";
	add_assoc_long(return_value, key, mrch.mx);
	key = "my";
	add_assoc_long(return_value, key, mrch.my);
	key = "mz";
	add_assoc_long(return_value, key, mrch.mz);
	key = "x_length";
	add_assoc_double(return_value, key, mrch.x_length);
	key = "y_length";
	add_assoc_double(return_value, key, mrch.y_length);
	key = "z_length";
	add_assoc_double(return_value, key, mrch.z_length);
	key = "alpha";
	add_assoc_double(return_value, key, mrch.alpha);
	key = "beta";
	add_assoc_double(return_value, key, mrch.beta);
	key = "gamma";
	add_assoc_double(return_value, key, mrch.gamma);
	key = "mapc";
	add_assoc_long(return_value, key, mrch.mapc);
	key = "mapr";
	add_assoc_long(return_value, key, mrch.mapr);
	key = "maps";
	add_assoc_long(return_value, key, mrch.maps);
	key = "amin";
	add_assoc_double(return_value, key, mrch.amin);
	key = "amax";
	add_assoc_double(return_value, key, mrch.amax);
	key = "amean";
	add_assoc_double(return_value, key, mrch.amean);
	key = "ispg";
	add_assoc_long(return_value, key, mrch.ispg);
	key = "nsymbt";
	add_assoc_long(return_value, key, mrch.nsymbt);
	key = "xorigin";
	add_assoc_double(return_value, key, mrch.xorigin);
	key = "yorigin";
	add_assoc_double(return_value, key, mrch.yorigin);
	key = "zorigin";
	add_assoc_double(return_value, key, mrch.zorigin);
	key = "map";
	add_assoc_string(return_value, key, mrch.map, 1);
	key = "mapstamp";
	add_assoc_string(return_value, key, mrch.machstamp, 1);
	key = "rms";
	add_assoc_double(return_value, key, mrch.rms);
	key = "nlabl";
	add_assoc_long(return_value, key, mrch.nlabl);
}


/* {{{ vim options
 * Local variables:
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
}}} */
