/*
  +----------------------------------------------------------------------+
  | PHP Version 4                                                        |
  +----------------------------------------------------------------------+
  | Copyright (c) 1997-2003 The PHP Group                                |
  +----------------------------------------------------------------------+
  | This source file is subject to version 2.02 of the PHP license,      |
  | that is bundled with this package in the file LICENSE, and is        |
  | available at through the world-wide-web at                           |
  | http://www.php.net/license/2_02.txt.                                 |
  | If you did not receive a copy of the PHP license and are unable to   |
  | obtain it through the world-wide-web, please send a note to          |
  | license@php.net so we can mail you a copy immediately.               |
  +----------------------------------------------------------------------+
  | Author:                                                              |
  +----------------------------------------------------------------------+

  $Id: php_mrc.c,v 1.2 2005-02-23 02:03:28 dfellman Exp $ 
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


/* {{{ mrc_functions[]
 *
 * Every user visible function must have an entry in mrc_functions[].
 */
function_entry mrc_functions[] = {
	ZEND_FE(imagecreatefrommrc, NULL)
        ZEND_FE(imagefilteredcreatefrommrc, NULL)
        ZEND_FE(imagemrcinfo, NULL)
        ZEND_FE(imagefiltergaussian, NULL)
        ZEND_FE(imagefastcopyresized, NULL)
        ZEND_FE(imagescale, NULL)
        ZEND_FE(logscale, NULL)
#ifdef HAVE_FFTW
        ZEND_FE(getfft, NULL)
        ZEND_FE(imagecreatefftfrommrc, NULL)
#endif
	{NULL, NULL, NULL}	/* Must be the last line in mrc_functions[] */
};
/* }}} */

/* {{{ mrc_module_entry
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
	"0.1", /* Replace with version number for your extension */
#endif
	STANDARD_MODULE_PROPERTIES
};
/* }}} */

#ifdef COMPILE_DL_MRC
ZEND_GET_MODULE(mrc)
#endif

/* {{{ PHP_INI
 */
/* Remove comments and fill if you need to have entries in php.ini
PHP_INI_BEGIN()
    STD_PHP_INI_ENTRY("mrc.global_value",      "42", PHP_INI_ALL, OnUpdateInt, global_value, zend_mrc_globals, mrc_globals)
    STD_PHP_INI_ENTRY("mrc.global_string", "foobar", PHP_INI_ALL, OnUpdateString, global_string, zend_mrc_globals, mrc_globals)
PHP_INI_END()
*/
/* }}} */

/* {{{ php_mrc_init_globals
 */
/* Uncomment this function if you have INI entries
static void php_mrc_init_globals(zend_mrc_globals *mrc_globals)
{
	mrc_globals->global_value = 0;
	mrc_globals->global_string = NULL;
}
*/
/* }}} */

/* {{{ PHP_MINIT_FUNCTION
 */
PHP_MINIT_FUNCTION(mrc)
{
	le_gd = zend_fetch_list_dtor_id("gd"); 
	/* If you have INI entries, uncomment these lines 
	ZEND_INIT_MODULE_GLOBALS(mrc, php_mrc_init_globals, NULL);
	REGISTER_INI_ENTRIES();
	*/
	return SUCCESS;
}
/* }}} */

/* {{{ PHP_MSHUTDOWN_FUNCTION
 */
PHP_MSHUTDOWN_FUNCTION(mrc)
{
	/* uncomment this line if you have INI entries
	UNREGISTER_INI_ENTRIES();
	*/
	return SUCCESS;
}
/* }}} */

/* Remove if there's nothing to do at request start */
/* {{{ PHP_RINIT_FUNCTION
 */
PHP_RINIT_FUNCTION(mrc)
{
	return SUCCESS;
}
/* }}} */

/* Remove if there's nothing to do at request end */
/* {{{ PHP_RSHUTDOWN_FUNCTION
 */
PHP_RSHUTDOWN_FUNCTION(mrc)
{
	return SUCCESS;
}
/* }}} */

/* {{{ PHP_MINFO_FUNCTION
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
/* }}} */


/* Remove the following function when you have succesfully modified config.m4
   so that your module can be compiled into PHP, it exists only for testing
   purposes. */

/* Every user-visible function in PHP should document itself in the source */

/* 
{{{ imagecreatefrommrc -- Create a new image from MRC file, URL or a String, with rescaling options.
Description:
	resource imagecreatefrommrc ( string data [, int pmin [, int pmax [, int binning [, boolean skip]]]])
	(image resource compatible with gd library)
*/
ZEND_FUNCTION(imagecreatefrommrc)
{
	zval **data, **PMIN, **PMAX, **BINNING, **SKIP_AVRG, **COLOR_MAP;
	gdIOCtx *io_ctx;
	MRC mrc;
	gdImagePtr im;
	char *ptfile;
	int argc = ZEND_NUM_ARGS();
	int nWidth = 0;
        int nHeight = 0;
	int minPix=densityMIN, maxPix = -1;
	int binning = 1;
	int skip_avrg = 0;
	int colormap = 0;

	if (argc < 1 || argc > 6) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &PMIN, &PMAX, &COLOR_MAP, &BINNING, &SKIP_AVRG);

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
	if (argc>4) {
		convert_to_long_ex(BINNING);
		binning = Z_LVAL_PP(BINNING);
	}
	if (argc>5) {
		convert_to_boolean_ex(SKIP_AVRG);
		skip_avrg = Z_LVAL_PP(SKIP_AVRG);
	}

	if (binning <= 0) 
		zend_error(E_ERROR, "%s(): binning must be greater than 0", get_active_function_name(TSRMLS_C));

	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}

	if(gdreadMRCHeader(io_ctx, &(mrc.header))==-1) {

		/* not a mrc string header */
		ptfile = (char *)((*data)->value.str.val);
		if(loadMRC(ptfile, &mrc)==-1) {
			zend_error(E_ERROR, "%s(): %s : No such file or directory ",
					 get_active_function_name(TSRMLS_C),ptfile);
		}

	} else if(gdreadMRCData(io_ctx, &mrc)==-1) {
		zend_error(E_ERROR, "%s(): Input is not a MRC string ",
				 get_active_function_name(TSRMLS_C));
	}

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
        nWidth = mrc.header.nx/binning;
        nHeight = mrc.header.ny/binning;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	mrc_to_image(&mrc, im->tpixels, minPix , maxPix, binning, skip_avrg, 0, 0, colormap);
	free(mrc.pbyData);
	free(io_ctx);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */

#ifdef HAVE_FFTW
/* 
{{{ imagecreatefftfrommrc -- Generate FFT image from MRC file, URL or a String, with rescaling options.
Description:
	resource imagecreatefftfrommrc ( string data [, int mask_rad [, int pmin [, int pmax [, int color_map ]]]])
	(image resource compatible with gd library)
*/
ZEND_FUNCTION(imagecreatefftfrommrc)
{
	zval **data, **MASK_RAD, **PMIN, **PMAX, **COLOR_MAP;
	gdIOCtx *io_ctx;
	MRC mrc;
	gdImagePtr im;
	char *ptfile;
	int argc = ZEND_NUM_ARGS();
	int nWidth = 0;
        int nHeight = 0;
	int minPix=densityMIN, maxPix = -1;
	int binning = 1;
	int skip_avrg = 0;
	int colormap = 0;
	int mask_radius = 0;

	if (argc < 1 || argc > 5) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &MASK_RAD, &PMIN, &PMAX, &COLOR_MAP);

	if (argc>1) {
		convert_to_long_ex(MASK_RAD);
		mask_radius = Z_LVAL_PP(MASK_RAD);
	}
	if (argc>2) {
		convert_to_long_ex(PMIN);
		minPix = Z_LVAL_PP(PMIN);
	}
	if (argc>3) {
		convert_to_long_ex(PMAX);
		maxPix = Z_LVAL_PP(PMAX);
	}
	if (argc>4) {
		convert_to_long_ex(COLOR_MAP);
		colormap = Z_LVAL_PP(COLOR_MAP);
	}

	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}

	if(gdreadMRCHeader(io_ctx, &(mrc.header))==-1) {

		/* not a mrc string header */
		ptfile = (char *)((*data)->value.str.val);
		if(loadMRC(ptfile, &mrc)==-1) {
			zend_error(E_ERROR, "%s(): %s : No such file or directory ",
					 get_active_function_name(TSRMLS_C),ptfile);
		}

	} else if(gdreadMRCData(io_ctx, &mrc)==-1) {
		zend_error(E_ERROR, "%s(): Input is not a MRC string ",
				 get_active_function_name(TSRMLS_C));
	}

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
        nWidth = mrc.header.nx/binning;
        nHeight = mrc.header.ny/binning;
	
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	if (0) {
	Info pInfo;
	fftw_info(&mrc, &pInfo, mask_radius); 
	zend_printf("info minval %f <br>", pInfo.minval);
	zend_printf("info maxval  %f <br>", pInfo.maxval);
	zend_printf("info nminval %f <br>", pInfo.nminval);
	zend_printf("info nmaxval  %f <br>", pInfo.nmaxval);
	zend_printf("info stddev  %f <br>", pInfo.stddev);
	zend_printf("info avg  %f <br>", pInfo.avg);
	zend_printf("info scale %f <br>", pInfo.scale);
	zend_printf("info n %d <br>", pInfo.n);
	return;
	}

	mrc_to_fftw_image(&mrc, im->tpixels, mask_radius, minPix, maxPix, colormap); 
	free(mrc.pbyData);
	free(io_ctx);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */
#endif

/* 
{{{ imagefilteredcreatefrommrc -- Create a new image from MRC file, URL or a String, with rescaling
and filtering options.
Description:
	resource imagefilteredcreatefrommrc
		( string data [, int pmin [, int pmax [, int binning [, int kernel [, float sigma]]]]])
	(image resource compatible with gd library)

*/
ZEND_FUNCTION(imagefilteredcreatefrommrc)
{
	zval **data, **PMIN, **PMAX, **COLOR_MAP, **BINNING, **KERNEL, **SIGMA;
	gdIOCtx *io_ctx;
	char *ptfile;
	MRC mrc;
	gdImagePtr im;
	int 	argc = ZEND_NUM_ARGS(),
		nWidth = 0,
		nHeight = 0,
		minPix = densityMIN,
		maxPix = densityColorMAX,
		binning = 1,
		kernel = 5;
	int colormap = 0;
	float	sigma = 1;

	if (argc < 1 || argc > 7) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &PMIN, &PMAX, &COLOR_MAP, &BINNING, &KERNEL, &SIGMA);

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
	if (argc>4) {
		convert_to_long_ex(BINNING);
		binning = Z_LVAL_PP(BINNING);
	}
	if (argc>5) {
		convert_to_long_ex(KERNEL);
		kernel = Z_LVAL_PP(KERNEL);
	}
	if (argc>6) {
		convert_to_double_ex(SIGMA);
		sigma = Z_DVAL_PP(SIGMA);
	}

	if (binning <= 0) 
		zend_error(E_ERROR, "%s(): binning must be greater than 0", get_active_function_name(TSRMLS_C));

	if (kernel % 2 != 1)
		zend_error(E_ERROR, "%s(): kernel must be an odd numner ", get_active_function_name(TSRMLS_C));

	if (sigma ==0)
		zend_error(E_ERROR, "%s(): sigma must be different than 0 ", get_active_function_name(TSRMLS_C));

	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}

	if(gdreadMRCHeader(io_ctx, &(mrc.header))==-1) {

		/* not a mrc string header
		maybe it is a file  */
		ptfile = (char *)((*data)->value.str.val);
		if(loadMRC(ptfile, &mrc)==-1) {
			zend_error(E_ERROR, "%s(): %s : No such file or directory ",
					 get_active_function_name(TSRMLS_C),ptfile);
		}

	} else if(gdreadMRCData(io_ctx, &mrc)==-1) {
		zend_error(E_ERROR, "%s(): Input is not a MRC string ",
				 get_active_function_name(TSRMLS_C));
	}

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
        nWidth = mrc.header.nx/binning;
        nHeight = mrc.header.ny/binning;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);
	mrc_to_image(&mrc, im->tpixels, minPix, maxPix, binning, 1, kernel, sigma, colormap);
	free(mrc.pbyData);
	free(io_ctx);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);
}
/* }}} */

/*
{{{ imagemrcinfo -- retrieve MRC header information MRC file, URL or a String,
	as a PHP associative array.
Description:
	array imagecreatefrommrc ( string data )
*/
ZEND_FUNCTION(imagemrcinfo)
{
	zval **data;
	gdIOCtx *io_ctx;
	MRCHeader mrch;
	char *ptfile;
	char *key;
	int val;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &data) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}
	if(gdreadMRCHeader(io_ctx, &mrch)==-1) {
		/* not a mrc string header */
		ptfile = (char *)((*data)->value.str.val);
		if(loadMRCHeader(ptfile, &mrch)==-1) 
			zend_error(E_ERROR, "%s(): %s : No such file or directory ",
				 get_active_function_name(TSRMLS_C),ptfile);
	}
	free(io_ctx);

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
	key = "extra[MRC_USER]";
	add_assoc_long(return_value, key, mrch.extra[MRC_USER]);
	key = "xorigin";
	add_assoc_double(return_value, key, mrch.xorigin);
	key = "yorigin";
	add_assoc_double(return_value, key, mrch.yorigin);
	key = "nlabl";
	add_assoc_long(return_value, key, mrch.nlabl);


}
/* }}} */


/*
{{{ imagefastcopyresized -- Copy and resize part of an image
Description
int imagefastcopyresized ( resource dst_im, resource src_im, int dstX, int dstY, int srcX, int srcY, int dstW, int dstH, int srcW, int srcH)
*/
ZEND_FUNCTION(imagefastcopyresized)
{
    zval **SIM, **DIM, **SX, **SY, **SW, **SH, **DX, **DY, **DW, **DH;
    gdImagePtr im_dst, im_src;
    int srcH, srcW, dstH, dstW, srcY, srcX, dstY, dstX;

    if (ZEND_NUM_ARGS() != 10 ||
        zend_get_parameters_ex(10, &DIM, &SIM, &DX, &DY, &SX, &SY, &DW, &DH, &SW, &SH) == FAILURE) {
        ZEND_WRONG_PARAM_COUNT();
    }

    ZEND_FETCH_RESOURCE(im_dst, gdImagePtr, DIM, -1, "Image", le_gd);
    ZEND_FETCH_RESOURCE(im_src, gdImagePtr, SIM, -1, "Image", le_gd);

    convert_to_long_ex(SX);
    convert_to_long_ex(SY);
    convert_to_long_ex(SW);
    convert_to_long_ex(SH);
    convert_to_long_ex(DX);
    convert_to_long_ex(DY);
    convert_to_long_ex(DW);
    convert_to_long_ex(DH);

    srcX = Z_LVAL_PP(SX);
    srcY = Z_LVAL_PP(SY);
    srcH = Z_LVAL_PP(SH);
    srcW = Z_LVAL_PP(SW);
    dstX = Z_LVAL_PP(DX);
    dstY = Z_LVAL_PP(DY);
    dstH = Z_LVAL_PP(DH);
    dstW = Z_LVAL_PP(DW);

    gdImageFastCopyResized(im_dst, im_src, dstX, dstY, srcX, srcY, dstW, dstH, srcW, srcH);
    RETURN_TRUE;
}
/* }}} */

/*
{{{ imagefiltergaussian -- apply gaussian filter to an image
Description:
	int imagefiltergaussian ( resource image [, int kernel [, float sigma ]])

*/
ZEND_FUNCTION(imagefiltergaussian)
{
	zval **imgind, **KERNEL, **SIGMA;
	gdImagePtr im;
	int argc = ZEND_NUM_ARGS();
	int	kernel;
	float	sigma;

	if (argc < 3 ) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &imgind, &KERNEL, &SIGMA);

	convert_to_long_ex(KERNEL);
	convert_to_double_ex(SIGMA);
	kernel = Z_LVAL_PP(KERNEL);
	sigma = Z_DVAL_PP(SIGMA);

	if (sigma == 0) 
		zend_error(E_ERROR, "%s(): sigma cannot be 0", get_active_function_name(TSRMLS_C));

	if (kernel % 2 != 1)
		zend_error(E_ERROR, "%s(): kernel must be an odd number", get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(im, gdImagePtr, imgind, -1, "Image", le_gd);

	filtergaussian(im, kernel, sigma);

	RETURN_TRUE;
}
/* }}} */

/*
{{{ imagescale -- scale an image
Description:
	int imagescale ( resource image , float scalefactorX[, float scalefactorY]])

*/
ZEND_FUNCTION(imagescale)
{
	zval **imgind, **SFX, **SFY;
	gdImagePtr im_dst, im_src;
	int	w, h, nw, nh,
		argc = ZEND_NUM_ARGS();
	float	scalefactorx,
		scalefactory;

	if (argc < 2 || argc > 3 ) 
	{
		WRONG_PARAM_COUNT;
	} 
	zend_get_parameters_ex(argc, &imgind, &SFX, &SFY);
	convert_to_double_ex(SFX);
	scalefactorx = Z_DVAL_PP(SFX);

	if (argc==3) {
		convert_to_double_ex(SFY);
		scalefactory = Z_DVAL_PP(SFY);
	} else {
		scalefactory = scalefactorx;
	}
	if (scalefactorx < 0 || scalefactory < 0)
		zend_error(E_ERROR, "%s(): scale factor must be greater than 0",
				get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(im_src, gdImagePtr, imgind, -1, "Image", le_gd);

	w = im_src->sx;
	h = im_src->sy;
	nw = w*scalefactorx;
	nh = w*scalefactory;

	im_dst = gdImageCreateTrueColor(nw, nh);
	gdImageFastCopyResized(im_dst, im_src, 0, 0, 0, 0, nw, nh, w, h);
	gdImageDestroy(im_src);
	im_src = gdImageCreateTrueColor(nw, nh);
	copytpixels(im_src, im_dst);
	gdImageDestroy(im_dst);
	RETURN_TRUE;
}
/* }}} */

/*
{{{ logscale -- scale an image with log
Description:
	int logscale ( resource image )
*/
ZEND_FUNCTION(logscale)
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
/* }}} */

#ifdef HAVE_FFTW
/*
{{{ getfft -- generate FFT from a existing image resource.
Description:
	int getfft ( resource image )
*/
ZEND_FUNCTION(getfft)
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

	getfft(im_src);
	RETURN_TRUE;
}
/* }}} */
#endif
