#!/usr/bin/env python
import time
import FFT
import FFT2
from MLab import rand

print "1-D comparison:\n"
fft_start = time.time()
for k in range(0,100):
    b = FFT.fft2d(rand(1024,1))
fft_end = time.time()

fftw_start = time.time()
for k in range(0,100):
    b = FFT2.fft2d(rand(1024,1))
fftw_end = time.time()

dif1 = fft_end - fft_start
dif2 = fftw_end - fftw_start
print "FFT:  " + repr(round(dif1,4)) + " seconds"
print "FFT2: " + repr(round(dif2,4)) + " seconds"
print "FFT2  is " + repr(round((dif1-dif2)/dif1*100,2)) + "% faster.\n"
print "******************\n"


print "2-D comparison:\n"
fft_start = time.time()
for k in range(0,100):
    b = FFT.fft2d(rand(128,128))
fft_end = time.time()

fftw_start = time.time()
for k in range(0,100):
    b = FFT2.fft2d(rand(128,128))
fftw_end = time.time()

dif1 = fft_end - fft_start
dif2 = fftw_end - fftw_start
print "FFT:  " + repr(round(dif1,4)) + " seconds"
print "FFT2: " + repr(round(dif2,4)) + " seconds"
print "FFT2  is " + repr(round((dif1-dif2)/dif1*100,2)) + "% faster.\n"







