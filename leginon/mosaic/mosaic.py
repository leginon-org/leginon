import Numeric

# i = x = row
# j = y = column

def add_piece(target,source,txoff,tyoff,theta,sclx,scly,thresh,txmin,txmax,tymin,tymax):
	print 'TARGET TYPECODE', target.typecode()
	targetimg = target.flat
	tshapeint0, tshapeint1 = target.shape
	tshape0 = Numeric.array(target.shape[0], Numeric.Float32)
	tshape1 = Numeric.array(target.shape[1], Numeric.Float32)
	tnpix = len(targetimg)
	txrnge = Numeric.array(txmax - txmin, Numeric.Float32)
	tyrnge = Numeric.array(tymax - tymin, Numeric.Float32)

	print 'SOURCE TYPECODE', source.typecode()
	sourceimg = source.flat
	sshapeint0,sshapeint1 = source.shape
	sshape0 = Numeric.array(source.shape[0], Numeric.Float32)
	sshape1 = Numeric.array(source.shape[1], Numeric.Float32)
	#sshape = Numeric.array(source.shape, Numeric.Float32)
	#sshape.shape = (-1,1)

	resx = Numeric.array(1.0 / (2.0 * sshape0) - 0.5, Numeric.Float32)
	resy = Numeric.array(1.0 / (2.0 * sshape1) - 0.5, Numeric.Float32)

	sintheta = Numeric.array(Numeric.sin(theta), Numeric.Float32)
	costheta = Numeric.array(Numeric.cos(theta), Numeric.Float32)
	sclx = Numeric.array(sclx, Numeric.Float32)
	scly = Numeric.array(scly, Numeric.Float32)
	txoff = Numeric.array(txoff, Numeric.Float32)
	tyoff = Numeric.array(tyoff, Numeric.Float32)
	txmin = Numeric.array(txmin, Numeric.Float32)
	txmax = Numeric.array(txmax, Numeric.Float32)
	tymin = Numeric.array(tymin, Numeric.Float32)
	tymax = Numeric.array(tymax, Numeric.Float32)

	jarray = range(sshapeint1)
	jarray = map(lambda x: Numeric.array(x, Numeric.Float32), jarray)
	iarray = range(sshapeint0)
	iarray = map(lambda x: Numeric.array(x, Numeric.Float32), iarray)

	print "LOOP"
	for j in jarray:
		jint = int(j)
		y = j / sshape1 + resy
		ysintheta = y * sintheta
		ycostheta = y * costheta
		for i in iarray:
			iint = int(i)
			icnt = jint * sshapeint0 + iint
			continue
			if sourceimg[icnt] < thresh:
				continue

			x =  i / sshape0 + resx 

			tx =  x * costheta + ysintheta
			ty =  x * sintheta - ycostheta

			## should this be integer math?
			tx = sshape0 * sclx * tx + txoff
			ty = sshape1 * scly * ty + tyoff

			itx = tshape0 * (tx - txmin) / txrnge
			ity = tshape1 * (ty - tymin) / tyrnge

			itcnt = ity * tshape0 + itx
			itcnt = int(itcnt[0])

			if (itcnt > 0) and (itcnt < tnpix):
				targetimg[itcnt] = sourceimg[icnt]
	print "DONE"
