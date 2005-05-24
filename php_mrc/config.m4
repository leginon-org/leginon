dnl $Id: config.m4,v 1.4 2005-05-24 19:48:40 dfellman Exp $
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
          test -f "$i/include/sfftw.h" && test -f "$i/include/srfftw.h" && FFTW_DIR=$i && break
	done
	if test -z "$FFTW_DIR"; then
		AC_MSG_ERROR([sfftw.h or srfftw.h not found.])
	else
		AC_MSG_RESULT(FFTW_DIR  found)
		for i in /usr/local/lib /usr/lib; do
		  test -f "$i/libsrfftw.so" && test -f "$i/libsfftw.so" && FFTW_LIB_DIR=$i && break
		done
		if test "$FFTW_LIB_DIR"; then
			AC_MSG_RESULT(FFTW_LIB_DIR found)
			PHP_CHECK_LIBRARY(sfftw, fftw_make_plan,
			[
				AC_DEFINE(HAVE_FFTW,1,[ ])
			], [
				AC_MSG_ERROR([Problem with sfftw.(a|so) or srfftw.(a|so). Please check config.log for more information.])
			], [
				-L$FFTW_LIB_DIR -lsrfftw -lsfftw -lm
			])
			fft_source="fft.c"
		fi
	fi
	for i in /usr/include/php/ext/gd/libgd; do
		test -f "$i/gd.h" && GD_DIR=$i && break
	done
	if test -z "$GD_DIR"; then
		AC_MSG_ERROR([gd.h not found.])
	else
		AC_MSG_RESULT(GD_DIR  found)
	fi
	PHP_ADD_LIBRARY_WITH_PATH(sfftw, $FFTW_LIB_DIR, MRC_SHARED_LIBADD)
	PHP_ADD_LIBRARY_WITH_PATH(srfftw, $FFTW_LIB_DIR, MRC_SHARED_LIBADD)
	PHP_ADD_INCLUDE($FFTW_DIR/include)
	PHP_ADD_INCLUDE($GD_DIR)
	PHP_SUBST(MRC_SHARED_LIBADD)
	PHP_NEW_EXTENSION(mrc, php_mrc.c mrc.c gd_mrc.c filter.c $fft_source, $ext_shared)
fi
