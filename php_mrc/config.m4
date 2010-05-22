dnl $Id: config.m4,v 1.8 2006/05/19 18:41:43 dfellman Exp $
dnl config.m4 for extension mrcmod

dnl Comments in this file start with the string 'dnl'.
dnl Remove where necessary. This file will not work
dnl without editing.

dnl If your extension references something external, use with:

PHP_ARG_ENABLE(mrc, whether to enable mrc support,
[  --enable-mrc           Enable mrc support])

if test "$PHP_MRC" = "yes"; then
	AC_DEFINE(HAVE_MRCLIB,1,[ ])
	for i in /usr/local /usr; do
          test -f "$i/include/fftw3.h" && FFTW_DIR=$i && break
	done
	if test -z "$FFTW_DIR"; then
		AC_MSG_RESULT([sfftw.h or srfftw.h not found.])
	else
		AC_MSG_RESULT(FFTW_DIR  found... $FFTW_DIR)
		for i in /usr/local/lib /usr/lib /usr/lib64; do
		  test -f "$i/libfftw3.so" && FFTW_LIB_DIR=$i && break
		done
		if test "$FFTW_LIB_DIR"; then
			AC_MSG_RESULT(FFTW_LIB_DIR found... $FFTW_LIB_DIR)
			PHP_CHECK_LIBRARY(fftw3, fftw_plan_dft_1d,
			[
				AC_DEFINE(HAVE_FFTW,1,[ ])
			], [
				AC_MSG_ERROR([Problem with fftw3.(a|so). Please check config.log for more information.])
			], [
				-L$FFTW_LIB_DIR -lfftw3 -lm
			])
			fft_source="fft3.c"
		fi
	fi
dnl	for i in /usr/include; do
	for i in /usr/include/php/ext/gd/libgd; do
		test -f "$i/gd.h" && GD_DIR=$i && break
	done
	if test -z "$GD_DIR"; then
		AC_MSG_ERROR([gd.h not found.])
	else
		AC_MSG_RESULT(GD_DIR  found... $GD_DIR)
		for i in /usr/local/lib /usr/lib /usr/lib64; do
		  test -f "$i/libgd.so" && GD_LIB_DIR=$i && break
		done
		if test "$GD_LIB_DIR"; then
			AC_MSG_RESULT(GD_LIB_DIR found... $GD_LIB_DIR)
			PHP_CHECK_LIBRARY(gd, gdImageCreateTrueColor,
			[
				AC_DEFINE(HAVE_GD,1,[ ])
			], [
				AC_MSG_ERROR([Problem with libgd.(a|so). Please check config.log for more information.])
			], [
				-L$GD_LIB_DIR -lgd
			])
		fi
	fi
	PHP_ADD_LIBRARY_WITH_PATH(fftw3, $FFTW_LIB_DIR, MRC_SHARED_LIBADD)
dnl	PHP_ADD_LIBRARY_WITH_PATH(gd, $GD_LIB_DIR, MRC_SHARED_LIBADD)
	PHP_ADD_INCLUDE($FFTW_DIR/include)
	PHP_ADD_INCLUDE($GD_DIR)
	PHP_SUBST(MRC_SHARED_LIBADD)
	PHP_NEW_EXTENSION(mrc, php_mrc.c mrc.c gd_mrc.c filter.c $fft_source, $ext_shared)
fi
