#!/usr/bin/env python

import sys
import cv2
import numpy
import platform

print "system platform: ", platform.platform()
print "openCV version:  ", cv2.__version__

print "After import statements..."

detector = cv2.FeatureDetector_create("SIFT")
#detector = cv2.SIFT()
print "After creating SIFT feature detector..."
descriptor = cv2.DescriptorExtractor_create("BRIEF")
print "After creating BRIEF descriptor extractor..."
matcher = cv2.DescriptorMatcher_create("BruteForce-Hamming")
print "After creating BruteForce-Hamming descriptor matcher..."
data1 = numpy.random.random((128,128))
image1 = numpy.array(data1*256, dtype=numpy.uint8)
print "After numpy random image generation..."
kp1=detector.detect(image1)
print "After running the detector..."

print "We did it, openCV is working, congrats to all"
