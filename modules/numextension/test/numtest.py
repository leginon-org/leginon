#!/usr/bin/env python

import numpy
import numpy.testing
import numextension
import pyami.mrc
import pyami.imagefun
import sys
import math
import unittest

import numref

# decimal places required to be equal
precision = 7

class TestNumextension(unittest.TestCase):

  def setUp(self):
    sys.stdout.write("%s\n" % (sys.version,))
    self.ref = numref.reference
    self.input = pyami.mrc.read(self.ref['input_mrc'])

  def test_allstats(self):
    stats = numextension.allstats(self.input, min=True, max=True, mean=True, std=True)
    for name in ('min','max','mean','std'):
      sys.stdout.write("allstats %s: %s\n" % (name, stats[name]))
      self.assertAlmostEqual(stats[name], self.ref['allstats'][name], precision)

  def test_minmax(self):
    mn,mx = numextension.minmax(self.input)
    sys.stdout.write("minmax: %s, %s\n" % (mn,mx))
    self.assertAlmostEqual(mn,self.ref['minmax']['min'], precision)
    self.assertAlmostEqual(mx,self.ref['minmax']['max'], precision)

  def test_cannyedge(self):
    edgeimage,grad_mag = numextension.cannyedge(self.input, 1.8, 0.3, 0.9)
    pyami.mrc.write(edgeimage, "test_edge.mrc")
    pyami.mrc.write(grad_mag, "test_grad.mrc")
    ref_edge = pyami.mrc.read(self.ref['cannyedge']['edge_mrc'])
    numpy.testing.assert_almost_equal(edgeimage, ref_edge, precision)
    ref_grad = pyami.mrc.read(self.ref['cannyedge']['grad_mrc'])
    numpy.testing.assert_almost_equal(grad_mag, ref_grad, precision)

  def test_radialPower(self):
    pow = pyami.imagefun.power(self.input, 10)
    radpow = numextension.radialPower(pow, 0, 0)
    pyami.mrc.write(radpow, "test_radpow.mrc")
    ref_radpow = pyami.mrc.read(self.ref['radialPower']['mrc'])
    numpy.testing.assert_almost_equal(radpow, ref_radpow, precision)

  def test_bin(self):
    binned = numextension.bin(self.input, 4, 4)
    pyami.mrc.write(binned, "test_binned.mrc")
    ref_binned = pyami.mrc.read(self.ref['bin']['mrc'])
    numpy.testing.assert_almost_equal(binned, ref_binned, precision)

  def test_despike(self):
    imcopy = numpy.array(self.input)
    numextension.despike(imcopy, 11, 3.5, 1)
    pyami.mrc.write(imcopy, "test_despike.mrc")
    ref_despike = pyami.mrc.read(self.ref['despike']['mrc'])
    numpy.testing.assert_almost_equal(imcopy, ref_despike, precision)

  def test_logpolar(self):
    shape = self.input.shape
    args = (shape[0]//2, shape[0]//2, shape[0]/2.0, 0.0,
       min(shape[0]/2.0, shape[1]), -math.pi/2.0, math.pi/2.0)
    output, base, phiscale = numextension.logpolar(self.input, *args)
    pyami.mrc.write(output, "test_logpolar.mrc")
    sys.stdout.write("logpolar base,phiscale: %s, %s\n" % (base,phiscale))
    self.assertAlmostEqual(base, self.ref['logpolar']['base'], precision)
    self.assertAlmostEqual(phiscale, self.ref['logpolar']['phiscale'], precision)
    ref_logpolar = pyami.mrc.read(self.ref['logpolar']['mrc'])
    numpy.testing.assert_almost_equal(output, ref_logpolar, precision)

  def test_pointsInPolygon(self):
    polygon = ((0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0))
    # some points inside, some outside, and some on the edges
    points = ((0.0,0.0),(0.5,0.0),(1.0,0.0),(1.0,0.5),(1.0,1.0),
          (0.5,1.0),(0.0,1.0),(0.0,0.5),(-1.0,0.5),(0.5,0.5),
          (2.0,2.0),(0.5,-0.5))
    inside = numextension.pointsInPolygon(points, polygon)
    ref_inside = [False, True, True, True, False, False, False, False,
      False, True, False, False]
    self.assertSequenceEqual(inside, ref_inside)

  def test_hanning(self):
    han = numextension.hanning(4, 4, a=0.54)
    ref_hanning = numpy.array(
      [[0.00640001, 0.06160003, 0.06160003, 0.00640001],
       [0.06160003, 0.59289998, 0.59289998, 0.06160003],
       [0.06160004, 0.59290004, 0.59290004, 0.06160004],
       [0.00640001, 0.06160003, 0.06160003, 0.00640001]])
    numpy.testing.assert_almost_equal(han, ref_hanning, precision)

  def test_highpass(self):
    hp = numextension.highpass(4,4)
    ref_hp = numpy.array(
      [[ 2.        , 2.       ,  2.        , 2.        ],
       [ 0.37867966, 0.46693221, 0.75      , 1.26142919],
       [ 0.        , 0.08191483, 0.37867966, 0.99839634],
       [ 0.37867966, 0.46693221, 0.75      , 1.26142919]])
    numpy.testing.assert_almost_equal(hp, ref_hp, precision)

# run the tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestNumextension)
unittest.TextTestRunner(verbosity=2).run(suite)
