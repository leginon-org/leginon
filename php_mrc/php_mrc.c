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

  $Id: php_mrc.c,v 1.6 2005-09-15 23:48:20 dfellman Exp $ 
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
	ZEND_FE(imagecopyfrommrc, NULL)
	ZEND_FE(imagefilteredcreatefrommrc, NULL)
	ZEND_FE(imagemrcinfo, NULL)
	ZEND_FE(imagefiltergaussian, NULL)
	ZEND_FE(imagescale, NULL)
	ZEND_FE(logscale, NULL)
#ifdef HAVE_FFTW
	ZEND_FE(getfft, NULL)
    ZEND_FE(imagecreatefftfrommrc, NULL)
	ZEND_FE(mrcfftw, NULL)
#endif
	ZEND_FE(imagehistogramfrommrc, NULL)
	ZEND_FE(imagehistogram, NULL)
	ZEND_FE(mrcread, NULL)
	ZEND_FE(mrcwrite, NULL)
	ZEND_FE(mrccreate, NULL)
	ZEND_FE(mrcgaussianfilter, NULL)
	ZEND_FE(mrctoimage, NULL)
	ZEND_FE(mrccopy, NULL)
	ZEND_FE(mrcgetdata, NULL)
	ZEND_FE(mrcputdata, NULL)
	ZEND_FE(mrcgetinfo, NULL)
	ZEND_FE(mrcupdateheader, NULL)
	ZEND_FE(mrcdestroy, NULL)
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

/* {{{ php_free_mrc
 */
static void php_free_mrc(zend_rsrc_list_entry *rsrc TSRMLS_DC)
{
	mrc_destroy((MRCPtr)rsrc->ptr);
}
/* }}} */


/* {{{ PHP_MINIT_FUNCTION
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

/* {{{ imagecreatefrommrc -- Create a new image from MRC file, URL or a String, with rescaling options.
Description:
	resource imagecreatefrommrc ( string data [, int pmin [, int pmax [, int binning [, boolean skip]]]])
	(image resource compatible with gd library)
*/
ZEND_FUNCTION(imagecreatefrommrc)
{
	zval **data, **PMIN, **PMAX, **BINNING, **SKIP_AVRG, **COLOR_MAP;
	MRCPtr pmrc;
	gdImagePtr im;
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

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
	nWidth = pmrc->header.nx/binning;
	nHeight = pmrc->header.ny/binning;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	mrc_binning(pmrc, binning, skip_avrg);
	mrc_to_gd(pmrc, im->tpixels, minPix, maxPix, colormap);
	mrc_destroy(pmrc);

	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */

/* {{{ imagefilteredcreatefrommrc -- Create a new image from MRC file, URL or a String, with rescaling
and filtering options.
Description:
	resource imagefilteredcreatefrommrc
		( string data [, int pmin [, int pmax [, int binning [, int kernel [, float sigma]]]]])
	(image resource compatible with gd library)

*/
ZEND_FUNCTION(imagefilteredcreatefrommrc)
{
	zval **data, **PMIN, **PMAX, **COLOR_MAP, **BINNING, **KERNEL, **SIGMA;
	char *ptfile;
	MRCPtr pmrc;
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

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
	nWidth = pmrc->header.nx/binning;
	nHeight = pmrc->header.ny/binning;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	mrc_filter(pmrc, binning, kernel, sigma);
	mrc_to_gd(pmrc, im->tpixels, minPix, maxPix, colormap);
	mrc_destroy(pmrc);

	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */

/* {{{ imagecopyfrommrc -- Copy data from (x1,y1) (x2,y2) from a MRC file, URL or a String, with rescaling options.
Description:
	resource imagecopyfrommrc ( string data, int x1, int y1, int x2, int y2 [, int pmin [, int pmax [, int binning [, boolean skip]]]])
	(image resource compatible with gd library)
*/
ZEND_FUNCTION(imagecopyfrommrc)
{
	zval **data, **X1, **Y1, **X2, **Y2, **PMIN, **PMAX, **BINNING, **SKIP_AVRG, **COLOR_MAP;
	gdIOCtx *io_ctx;
	MRC mrc_src, mrc_dst;
	gdImagePtr im;
	char *ptfile;
	int argc = ZEND_NUM_ARGS();
	int nWidth = 0;
	int nHeight = 0;
	int x1=0, y1=0, x2=0, y2=0;
	int minPix=densityMIN, maxPix = -1;
	int binning = 1;
	int skip_avrg = 0;
	int colormap = 0;

	if (argc < 5 || argc > 10) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &X1, &Y1, &X2, &Y2, &PMIN, &PMAX, &COLOR_MAP, &BINNING, &SKIP_AVRG);

	if (argc>1) {
		convert_to_long_ex(X1);
		x1 = Z_LVAL_PP(X1);
	}
	if (argc>2) {
		convert_to_long_ex(Y1);
		y1 = Z_LVAL_PP(Y1);
	}
	if (argc>3) {
		convert_to_long_ex(X2);
		x2 = Z_LVAL_PP(X2);
	}
	if (argc>4) {
		convert_to_long_ex(Y2);
		y2 = Z_LVAL_PP(Y2);
	}
	if (argc>5) {
		convert_to_long_ex(PMIN);
		minPix = Z_LVAL_PP(PMIN);
	}
	if (argc>6) {
		convert_to_long_ex(PMAX);
		maxPix = Z_LVAL_PP(PMAX);
	}
	if (argc>7) {
		convert_to_long_ex(COLOR_MAP);
		colormap = Z_LVAL_PP(COLOR_MAP);
	}
	if (argc>8) {
		convert_to_long_ex(BINNING);
		binning = Z_LVAL_PP(BINNING);
	}
	if (argc>9) {
		convert_to_boolean_ex(SKIP_AVRG);
		skip_avrg = Z_LVAL_PP(SKIP_AVRG);
	}

	if (binning <= 0) 
		zend_error(E_ERROR, "%s(): binning must be greater than 0", get_active_function_name(TSRMLS_C));
	if (x1==x2 && y1==y2) 
		zend_error(E_ERROR, "%s(): (x1,y1) should be different than (x2,y2)", get_active_function_name(TSRMLS_C));
	if (x1<0 || x2<0 || y1<0 || y2<0)
		zend_error(E_ERROR, "%s(): x1,y1,x2,y2 must be strictly positive numbers", get_active_function_name(TSRMLS_C));

	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}

	if(gdreadMRCHeader(io_ctx, &(mrc_src.header))==-1) {

		/* not a mrc string header */
		ptfile = (char *)((*data)->value.str.val);
		if(loadMRC(ptfile, &mrc_src)==-1) {
			zend_error(E_ERROR, "%s(): %s : No such file or directory ",
					 get_active_function_name(TSRMLS_C),ptfile);
		}

	} else if(gdreadMRCData(io_ctx, &mrc_src)==-1) {
		zend_error(E_ERROR, "%s(): Input is not a MRC string ",
				 get_active_function_name(TSRMLS_C));
	}

	mrc_copy(&mrc_src, &mrc_dst, x1, y1, x2, y2);

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
	nWidth = mrc_dst.header.nx/binning;
	nHeight = mrc_dst.header.ny/binning;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	mrc_to_image(&mrc_dst, im->tpixels, minPix , maxPix, binning, skip_avrg, 0, 0, colormap);
	free(mrc_src.pbyData);
	free(mrc_dst.pbyData);
	free(io_ctx);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */

#ifdef HAVE_FFTW
/* {{{ imagecreatefftfrommrc -- Generate FFT image from MRC file, URL or a String, with rescaling options.
Description:
	resource imagecreatefftfrommrc ( string data [, int mask_rad [, int pmin [, int pmax [, int color_map ]]]])
	(image resource compatible with gd library)
*/
ZEND_FUNCTION(imagecreatefftfrommrc)
{
	zval **data, **MASK_RAD, **PMIN, **PMAX, **COLOR_MAP;
	MRCPtr pmrc;
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

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
	nWidth = pmrc->header.nx/binning;
	nHeight = pmrc->header.ny/binning;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	mrc_to_fftw_image(pmrc, im->tpixels, mask_radius, minPix, maxPix, colormap); 
	mrc_destroy(pmrc);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */

/* {{{ getfft -- generate FFT from a existing image resource.
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

/* {{{ mrcfftw(resource src_mrc, int mask) */
ZEND_FUNCTION(mrcfftw)
{

	zval	**data, **MASK;
	MRCPtr	pmrc;
	int	argc = ZEND_NUM_ARGS();
	int	mask = 0;

	if (argc != 2) 
	{
		WRONG_PARAM_COUNT;
	} 

	zend_get_parameters_ex(argc, &data, &MASK);

	convert_to_long_ex(MASK);
	mask = Z_LVAL_PP(MASK);

	if (mask < 0) 
		zend_error(E_ERROR, "%s(): mask must be greater than 0", get_active_function_name(TSRMLS_C));

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, data, -1, "MRCdata", le_mrc);
	mrc_fftw(pmrc, mask);
	mrc_update_header(pmrc);

}
/* }}} */
#endif

/* {{{ imagemrcinfo -- retrieve MRC header information MRC file, URL or a String,
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
/* }}} */

/* {{{ imagefiltergaussian -- apply gaussian filter to an image
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

/* {{{ imagescale -- scale an image
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

/* {{{ logscale -- scale an image with log
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

/* {{{ imagehistogram(resource image) */
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
/* }}} */

/* {{{ imagehistogramfrommrc(resource src_mrc) */
ZEND_FUNCTION(imagehistogramfrommrc)
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
/* }}} */

/* {{{ resource mrctoimage(resource src_mrc)
   */ 
PHP_FUNCTION(mrctoimage)
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

	maxPix = (maxPix<0) ?  ((colormap) ? densityColorMAX : densityMAX) : maxPix;
	nWidth = pmrc->header.nx;
	nHeight = pmrc->header.ny;
	
	im = gdImageCreateTrueColor(nWidth, nHeight);

	mrc_to_gd(pmrc, im->tpixels, minPix, maxPix, colormap);
	ZEND_REGISTER_RESOURCE(return_value, im, le_gd);

}
/* }}} */

/* {{{ createmrc(int x_size, int y_size)
   Create a new mrc image */
PHP_FUNCTION(mrccreate)
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
/* }}} */

/* {{{ resource mrcread(string filename, int binning [, bool skip_average] ) */
ZEND_FUNCTION(mrcread)
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

	pmrc = (MRC *) malloc (sizeof (MRC));
	_mrc_image_create_from(INTERNAL_FUNCTION_PARAM_PASSTHRU, data, pmrc);
	mrc_binning(pmrc, binning, skip_avg);

	ZEND_REGISTER_RESOURCE(return_value, pmrc, le_mrc);

}
/* }}} */

/* {{{ bool mrcwrite(resource src_mrc, string filename) */
PHP_FUNCTION(mrcwrite)
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
	
	writeMRC(fp, pmrc);

	fflush(fp);
	fclose(fp);
	RETURN_TRUE;
}
/* }}} */

/* {{{ bool mrcdestroy(resource src_mrc)
   Destroy an image */
PHP_FUNCTION(mrcdestroy)
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
/* }}} */

/* {{{ mrcgaussianfilter(resource src_mrc, int binning, int kernel, float sigma) */
ZEND_FUNCTION(mrcgaussianfilter)
{

	zval	**data, **BINNING, **KERNEL, **SIGMA;
	MRCPtr	pmrc;
	int	argc = ZEND_NUM_ARGS();
	int	kernel= 1;
	int	binning= 1;
	float	sigma;

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

}
/* }}} */

/* {{{ mrccopy(int dst_mrc, int src_mrc, int dst_x, int dst_y, int src_x, int src_y, int src_w, int src_h)
   Copy part of an mrc */ 
PHP_FUNCTION(mrccopy)
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
/* }}} */

/* {{{ mrcupdateheader(resource src_mrc) */ 
PHP_FUNCTION(mrcupdateheader)
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
/* }}} */

/* {{{ array mrcgetinfo(resource src_mrc) */
PHP_FUNCTION(mrcgetinfo)
{
	char *key;
	zval **MRCD;
	MRCPtr pmrc;
	MRCHeader mrch;

	if (ZEND_NUM_ARGS() != 1 || zend_get_parameters_ex(1, &MRCD) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}
	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

	mrch = pmrc->header;
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
/* }}} */

/* {{{ array mrcgetdata(resource src_mrc)*/ 
PHP_FUNCTION(mrcgetdata)
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
/* }}} */

/* {{{ mrcputdata(resource src_mrc, array data) */ 
PHP_FUNCTION(mrcputdata)
{
	zval	**MRCD, **input , **entry;
	MRCPtr	pmrc;
	MRCHeader	mrch;
	HashPosition pos;
	

        float	*data_array;

	double	n;

	int i,argc = ZEND_NUM_ARGS();

	if (ZEND_NUM_ARGS() != 2 || zend_get_parameters_ex(argc, &MRCD, &input) == FAILURE) {
		ZEND_WRONG_PARAM_COUNT();
	}


	if (Z_TYPE_PP(input) != IS_ARRAY) {
                zend_error(E_ERROR, "%s(): Input is not a MRC string ",
                                 get_active_function_name(TSRMLS_C));
	}

	ZEND_FETCH_RESOURCE(pmrc, MRCPtr, MRCD, -1, "MRCdata", le_mrc);

	data_array = (float *)pmrc->pbyData;
	n = mrch.nx * mrch.ny;

	/* Go through array array and add values to the return array */
	i=0;
	zend_hash_internal_pointer_reset_ex(Z_ARRVAL_PP(input), &pos);
	while (zend_hash_get_current_data_ex(Z_ARRVAL_PP(input), (void **)&entry, &pos) == SUCCESS) {

		(*entry)->refcount++;

		data_array[i] =  (float)Z_LVAL_PP(entry);

		zend_hash_move_forward_ex(Z_ARRVAL_PP(input), &pos);
		i++;
	}



}
/* }}} */

/* {{{ void _mrc_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pMRC) */
static void _mrc_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pMRC) {
	gdIOCtx *io_ctx;
	char *ptfile;

	convert_to_string_ex(data);
	io_ctx = gdNewDynamicCtx (Z_STRLEN_PP(data), Z_STRVAL_PP(data));
	if (!io_ctx) {
		RETURN_FALSE;
	}

	if(gdloadMRC(io_ctx, pMRC)==-1) {
		ptfile = (char *)((*data)->value.str.val);
		if(loadMRC(ptfile, pMRC)==-1) {
			zend_error(E_ERROR, "%s(): %s : No such file or directory or Input is not a MRC string ",
					 get_active_function_name(TSRMLS_C),ptfile);
		} 
	}
	free(io_ctx);
}
/* }}} */


/* {{{	vim options
 * Local variables:
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
}}} */
