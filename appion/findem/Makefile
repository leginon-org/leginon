f90=gfortran
f77=g77
cc=gcc
ar=ar cr
LPATH=.
BINPATH=../particle_manager
FFLAGS=-O3 -Wall -w -fno-second-underscore -mtune=pentium3 -mcpu=pentium3
CFLAGS=-O3 -Wall -mtune=pentium3 -mcpu=pentium3
LIBS=$(LPATH)/imlib2k.a $(LPATH)/ifftlib.a $(LPATH)/genlib.a $(LPATH)/misclib.a $(LPATH)/plot2klib.a
EXLIBS=-lg2c

quick:	clean findem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/findem.exe findem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/findem.exe

findem:	clean plot2k misc im2k ifft gen findem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/findem.exe findem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/findem.exe

old:	clean plot2k misc im2k ifft gen oldfindem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/oldfindem.exe oldfindem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/oldfindem.exe

all:	clean plot2k misc im2k ifft gen findem old

plot2k:	clean plot2k.c
	$(cc) $(CFLAGS) -c plot2k.c
	$(ar) $(LPATH)/plot2klib.a plot2k.o

misc:	clean plot2k mtzlib.for lcflib.for miscsubs.for
	$(f90) $(FFLAGS) -c lcflib.for
	$(f77) $(FFLAGS) -c mtzlib.for miscsubs.for
	$(ar) $(LPATH)/misclib.a lcflib.o mtzlib.o miscsubs.o

im2k:	clean imsubs2000.for imsubs2.for imsubs_common.for
	$(f90) $(FFLAGS) -c imsubs2000.for
	$(f77) $(FFLAGS) -c imsubs2.for
	$(ar) $(LPATH)/imlib2k.a imsubs2.o imsubs2000.o

ifft:	clean ifftsub.for
	$(f77) $(FFLAGS) -c ifftsub.for
	$(ar) $(LPATH)/ifftlib.a ifftsub.o

gen:	clean unix.for diskio.for ccplib.for subs.for parser.for symlib.for library.c library.h
	$(f77) $(FFLAGS) -c unix.for diskio.for subs.for parser.for symlib.for ccplib.for 
	$(cc) -c -O3 -DPROTOTYPE -Dalliant -w library.c
	$(ar) $(LPATH)/genlib.a diskio.o library.o parser.o subs.o symlib.o unix.o ccplib.o

clean:
	echo ""
	rm -f *~ *.mod
	#rm -f *.o *.a

distclean:
	rm -f *.o *~ *.mod
	rm -f $(LIBS) $(LPATH)/a.out 
	#rm -f $(BINPATH)/findem.exe findem.exe 

test:	$(BINPATH)/findem.exe
	$(BINPATH)/findem.exe < feedtest.txt
	echo ""; md5sum cccmaxmap001.mrc; echo "3dc23350d337ba98836507798562d33e"; echo "the above MD5SUMs should match"; echo ""
	rm -fv cccmaxmap001.mrc
