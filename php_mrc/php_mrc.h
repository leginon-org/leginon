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

  $Id: php_mrc.h,v 1.8 2005-10-11 17:07:48 dfellman Exp $ 
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

ZEND_FUNCTION(imagegaussianfilter);
ZEND_FUNCTION(imagescale);
ZEND_FUNCTION(imagelogscale);
ZEND_FUNCTION(imagehistogram);
#ifdef HAVE_FFTW
ZEND_FUNCTION(imagefftw);
ZEND_FUNCTION(mrcfftw);
#endif
ZEND_FUNCTION(mrcinfo);
ZEND_FUNCTION(mrcgetinfo);
ZEND_FUNCTION(mrcsx);
ZEND_FUNCTION(mrcsy);
ZEND_FUNCTION(mrcread);
ZEND_FUNCTION(mrcreadfromstring);
ZEND_FUNCTION(mrccreate);
ZEND_FUNCTION(mrcwrite);
ZEND_FUNCTION(mrctoimage);
ZEND_FUNCTION(mrccopy);
ZEND_FUNCTION(mrcbinning);
ZEND_FUNCTION(mrcgaussianfilter);
ZEND_FUNCTION(mrclogscale);
ZEND_FUNCTION(mrcgetdata);
ZEND_FUNCTION(mrcgetscale);
ZEND_FUNCTION(mrcputdata);
ZEND_FUNCTION(mrcupdateheader);
ZEND_FUNCTION(mrchistogram);
ZEND_FUNCTION(mrcdestroy);

static void _mrc_image_create_from(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc);
static void _mrc_image_create_from_string(INTERNAL_FUNCTION_PARAMETERS, zval **data, MRC *pmrc);
static void _mrc_header_data(INTERNAL_FUNCTION_PARAMETERS,  MRC *pmrc);

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
