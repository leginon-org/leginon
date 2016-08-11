#
# Makefile [array/mask]
#
# Copyright © 2012 Hanspeter Winkler
#


#
# definitions
#

include ../../Makedefs

PRFX = mask

INCS = $(PRFX).h $(PRFX)module.h $(PRFX)param.h

OBJS = $(PRFX).o $(PRFX)module.o mask_cmplx.o mask_ellips.o \
       mask_ellips_2d_cmplx.o mask_ellips_2d_real.o \
       mask_ellips_3d_cmplx.o mask_ellips_3d_real.o \
       mask_ellips_apod_2d_cmplx.o mask_ellips_apod_2d_real.o \
       mask_ellips_apod_3d_cmplx.o mask_ellips_apod_3d_real.o \
       mask_ellips_cmplx.o mask_ellips_real.o mask_gauss.o \
       mask_gauss_2d_cmplx.o mask_gauss_2d_real.o mask_gauss_3d_cmplx.o \
       mask_gauss_3d_real.o mask_gauss_cmplx.o mask_gauss_real.o \
       mask_real.o mask_rect.o mask_rect_2d_cmplx.o mask_rect_2d_real.o \
       mask_rect_3d_cmplx.o mask_rect_3d_real.o mask_rect_apod_2d_cmplx.o \
       mask_rect_apod_2d_real.o mask_rect_apod_3d_cmplx.o \
       mask_rect_apod_3d_real.o mask_rect_cmplx.o mask_rect_real.o \
       mask_stat_ellips_2d_real.o mask_stat_ellips_3d_real.o \
       mask_stat_rect_2d_real.o mask_stat_rect_3d_real.o \
       mask_stat_wedge_3d_real.o mask_wedge.o mask_wedge_3d_cmplx.o \
       mask_wedge_3d_real.o mask_wedge_apod_3d_cmplx.o \
       mask_wedge_apod_3d_real.o mask_wedge_cmplx.o mask_wedge_real.o \
       maskcommon.o maskparamnew.o maskparamstd.o maskparamwedge.o

CFLAGS = $(CLIBOPT)
CPPFLAGS = -I../config -I../../include $(CPPOPT)


#
# make rules
#

include ../../make/Makecommon.dirs


#
# build dependencies
#

-include Makedeps
