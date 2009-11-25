/*
  +----------------------------------------------------------------------+
  | PHP MRC Extension                                                    |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+

  $Id: php_mrc.h,v 1.16 2007/08/07 21:54:52 dfellman Exp $ 
*/

/**
 * \file php_mrc.h

	\brief PHP functions to manipulate MRC files.

	Introduction

	The php_mrc extension offers the functionalities to create, manipulate, filter and display MRC files.  
	If compiled with fftw3, the discrete Fourier transform can be computed and displayed "on the fly".

	Requirements

	- GD library
	- FFTW library

	Installation

	\include INSTALL


    Example1. Create a MRC file
    \htmlinclude mrccreate.html

    Example2. Read and Display a MRC file
    \htmlinclude mrcread.html

    Example3. Retrieve information from a MRC Header
    \htmlinclude mrcinfo.html

   
 */

#ifndef PHP_MRC_H
#define PHP_MRC_H

extern zend_module_entry mrc_module_entry;
#define phpext_mrc_ptr &mrc_module_entry

#ifdef PHP_WIN32
#define PHP_MRC_API __declspec(dllexport)
#else
#define PHP_MRC_API
#endif

#ifdef ZTS
#include "TSRM.h"
#endif

PHP_MINIT_FUNCTION(mrc);
PHP_MSHUTDOWN_FUNCTION(mrc);
PHP_RINIT_FUNCTION(mrc);
PHP_RSHUTDOWN_FUNCTION(mrc);
PHP_MINFO_FUNCTION(mrc);

ZEND_FUNCTION(gdimageinfo);
ZEND_FUNCTION(imagegaussianfilter);
ZEND_FUNCTION(imagehistogram);
ZEND_FUNCTION(imagegradient);
#ifdef HAVE_FFTW
ZEND_FUNCTION(mrcfftw);
#endif
ZEND_FUNCTION(mrcinfo);
ZEND_FUNCTION(mrcgetinfo);
ZEND_FUNCTION(mrcsx);
ZEND_FUNCTION(mrcsy);
ZEND_FUNCTION(mrcread);
ZEND_FUNCTION(mrcreadfromstring);
ZEND_FUNCTION(mrccreate);
ZEND_FUNCTION(imcreate);
ZEND_FUNCTION(mrcwrite);
ZEND_FUNCTION(mrcnormalize);
ZEND_FUNCTION(mrctoimage);
ZEND_FUNCTION(mrccopy);
ZEND_FUNCTION(mrccopyfromfile);
ZEND_FUNCTION(mrcbinning);
ZEND_FUNCTION(mrcgaussianfilter);
ZEND_FUNCTION(mrclogscale);
ZEND_FUNCTION(mrcgetdata);
ZEND_FUNCTION(mrcstdevscale);
ZEND_FUNCTION(mrcputdata);
ZEND_FUNCTION(mrcrotate);
ZEND_FUNCTION(mrcupdateheader);
ZEND_FUNCTION(mrcset);
ZEND_FUNCTION(mrchistogram);
ZEND_FUNCTION(mrccdfscale);
ZEND_FUNCTION(mrcdestroy);
ZEND_FUNCTION(imagicinfo);
ZEND_FUNCTION(imagicread);

static void _mrc_header_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRCHeader *pmrch);
static void _mrc_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc);
static void _mrc_image_create_from_string(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc);
static void _mrc_header_data(INTERNAL_FUNCTION_PARAMETERS,  MRC *pmrc);
static void _imagic_(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRCHeader *pmrch);
static void _imagic_header_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, Imagic5Header *pimagich, int img_num);
static void _imagic_header_data(INTERNAL_FUNCTION_PARAMETERS,  Imagic5Header imagich);
static void _imagic_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **heddata, zval **imgdata, int img_num, Imagic5one *pImagic5);

/* 
  	Declare any global variables you may need between the BEGIN
	and END macros here:     

ZEND_BEGIN_MODULE_GLOBALS(mrc)
	long  global_value;
	char *global_string;
ZEND_END_MODULE_GLOBALS(mrc)
*/

/* In every utility function you add that needs to use variables 
   in php_mrc_globals, call TSRMLS_FETCH(); after declaring other 
   variables used by that function, or better yet, pass in TSRMLS_CC
   after the last function argument and declare your utility function
   with TSRMLS_DC after the last declared argument.  Always refer to
   the globals in your function as MRC_G(variable).  You are 
   encouraged to rename these macros something shorter, see
   examples in any other php module directory.
*/

#ifdef ZTS
#define MRC_G(v) TSRMG(mrc_globals_id, zend_mrc_globals *, v)
#else
#define MRC_G(v) (mrc_globals.v)
#endif

#endif	/* PHP_MRC_H */


/*
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * indent-tabs-mode: t
 * End:
 */
