#!/usr/bin/env python

import sys
import cv2
import numpy
import platform

print "system platform: ", platform.platform()
print "openCV version:  ", cv2.__version__

detector = cv2.FeatureDetector_create("SIFT")
descriptor = cv2.DescriptorExtractor_create("BRIEF")
matcher = cv2.DescriptorMatcher_create("BruteForce-Hamming")
image1 = numpy.random.random((128,128))
kp1=detector.detect(image1)

print "We did it, openCV is working, congrats to all"
