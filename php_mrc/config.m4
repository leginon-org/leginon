dnl $Id: config.m4,v 1.2 2005-02-22 20:26:28 dfellman Exp $
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
dnl			PHP_CHECK_LIBRARY(fftw, rfftw2d_create_plan, [
dnl			AC_DEFINE(HAVE_FFTW,1,[ ])], [], [-L$FFTW_LIB_DIR -lsrfftw -lsfftw -lm])
			AC_DEFINE(HAVE_FFTW,1,[ ])
			fft_source="fft.c"
			MRCLIB_CFLAGS="-L$FFTW_LIB_DIR -lsrfftw -lsfftw -lm"
		fi
	fi
	PHP_NEW_EXTENSION(mrc, php_mrc.c mrc.c gd_mrc.c filter.c $fft_source, $ext_shared,, \\$(MRCLIB_CFLAGS))
	PHP_SUBST(MRCLIB_CFLAGS)
fi
