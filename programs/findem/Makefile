f90=gfortran
f77=g77
cc=gcc
ar=ar cr
LPATH=.
BINPATH=.
FFLAGS=-O3 -w -march=native -mtune=native
CFLAGS=-O3 -w -march=native -mtune=native
LIBS=$(LPATH)/imlib2010.a $(LPATH)/ifftlib.a $(LPATH)/genlib.a $(LPATH)/misclib.a $(LPATH)/plot2klib.a
ARCH=$(shell uname -i)
ifeq ($(ARCH),x86)
	EXENAME=findem32.exe
else
	EXENAME=findem64.exe
endif


quick:	findem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/$(EXENAME) findem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/$(EXENAME)

findem:	plot2k misc im2010 ifft gen findem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/$(EXENAME) findem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/$(EXENAME)

old:	plot2k misc im2010 ifft gen oldfindem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/oldfindem.exe oldfindem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/oldfindem.exe

all:	plot2k misc im2010 ifft gen findem

plot2k:	$(LPATH)/plot2klib.a
	$(cc) $(CFLAGS) -c plot2k.c
	$(ar) $(LPATH)/plot2klib.a plot2k.o

misc:	$(LPATH)/misclib.a
	$(f90) $(FFLAGS) -c lcflib.for
	$(f90) $(FFLAGS) -c mtzlib.for miscsubs.for
	$(ar) $(LPATH)/misclib.a lcflib.o mtzlib.o miscsubs.o

im2010:	$(LPATH)/imlib2010.a
	$(f90) $(FFLAGS) -c imsubs2010.for
	$(f90) $(FFLAGS) -c imsubs2.for
	$(ar) $(LPATH)/imlib2010.a imsubs2.o imsubs2010.o

ifft:	$(LPATH)/ifftlib.a
	$(f90) $(FFLAGS) -c ifftsub.for
	$(ar) $(LPATH)/ifftlib.a ifftsub.o

gen:	$(LPATH)/genlib.a
	$(f90) $(FFLAGS) -c unix.for diskio.for subs.for parser.for symlib.for ccplib.for 
	$(cc) -c -O3 -DPROTOTYPE -Dalliant -w library.c
	$(ar) $(LPATH)/genlib.a diskio.o library.o parser.o subs.o symlib.o unix.o ccplib.o

clean:
	rm -fv *~ *.mod
	#rm -fv *.o *.a
	rm -fv cccmaxmap001.mrc

distclean:
	rm -fv *.o *~ *.mod
	rm -fv $(LIBS) $(LPATH)/a.out 
	#rm -fv $(BINPATH)/$(EXENAME) $(EXENAME)
	rm -fv cccmaxmap001.mrc

test:	$(BINPATH)/$(EXENAME)
	rm -fv cccmaxmap001.mrc
	$(BINPATH)/$(EXENAME) < feedtest.txt

