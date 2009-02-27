f90=gfortran
f77=g77
cc=gcc
ar=ar cr
LPATH=.
BINPATH=../bin
FFLAGS=-O3 -Wall -w -fno-second-underscore
CFLAGS=-O3 -Wall
LIBS=$(LPATH)/imlib2k.a $(LPATH)/ifftlib.a $(LPATH)/genlib.a $(LPATH)/misclib.a $(LPATH)/plot2klib.a
## CentOS 5
EXLIBS=-L/usr/lib/gcc/i386-redhat-linux/3.4.6/ -lg2c
#EXLIBS=-L/usr/lib/gcc/x86_64-redhat-linux/3.4.6/ -lg2c
## Fedora 10
#EXLIBS=-L/usr/lib64 -L/usr/lib/gcc/x86_64-redhat-linux/3.4.6/ -lg2c

findem:	clean plot2k misc im2k ifft gen findem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/findem.exe findem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/findem.exe

quick:	clean findem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/findem.exe findem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/findem.exe

old:	clean plot2k misc im2k ifft gen oldfindem.f90
	$(f90) $(FFLAGS) $(EXLIBS) -o $(BINPATH)/oldfindem.exe oldfindem.f90 $(LIBS) 
	chmod 777 $(BINPATH)/oldfindem.exe

all:	clean plot2k misc im2k ifft gen findem

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
	rm -fv *~ *.mod
	#rm -fv *.o *.a
	rm -fv cccmaxmap001.mrc

distclean:
	rm -fv *.o *~ *.mod
	rm -fv $(LIBS) $(LPATH)/a.out 
	#rm -fv $(BINPATH)/findem.exe findem.exe 
	rm -fv cccmaxmap001.mrc

test:	$(BINPATH)/findem.exe
	rm -fv cccmaxmap001.mrc
	$(BINPATH)/findem.exe < feedtest.txt
	#echo ""; md5sum cccmaxmap001.mrc; echo "2a2f0482ab92e4b9cc9b5990c7a7de42"; echo "the above MD5SUMs should match"; echo ""
