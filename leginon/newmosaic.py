import math

def add_piece(target, source, gxoff, gyoff, theta, sclx, scly, thresh,
																						gxmin, gxmax, gymin, gymax):

#	gimg = target.flat			# 1-D array of the entire mosaic image
	gimg = target						# 1-D array of the entire mosaic image
	# flipped?
	gnx = target.shape[1]		# mosaic image x dimension size
	gny = target.shape[0]		# mosaic image y dimension size
	gnpix = gnx * gny				# mosaic image number of total elements

	gxrnge = gxmax - gxmin	# range of the stage x-axis
	gyrnge = gymax - gymin	# range of the stage y-axis

#	img = source.flat				# 1-D array of the image to be added
	img = source						# 1-D array of the image to be added
	# flipped?
	nx = source.shape[1]		# image to be added x dimension size
	ny = source.shape[0]		# image to be added y dimension size

	resx = 1.0 / (2.0 * nx) - 0.5		# (1 / (2 * source image x size)) - 0.5
	resy = 1.0 / (2.0 * ny) - 0.5		# (1 / (2 * source image y size)) - 0.5

	sintheta = math.sin(theta)			# sine of the source image angle
	costheta = math.cos(theta)			# cosine of the source image angle

	# ints
#	icnt = 0								# element number in image to be added
#	igcnt = 0								# element number in mosaic image
	igx = 0
	igy = 0

	# floats
	x = 0.
	y = 0.
	gx = 0.
	gy = 0.

	# for each element in y-axis of image to be added
	# for row in image to be added
	for j in xrange(ny):

		# y = (row number / number of rows) + (1 / (2 * number of rows)) - 0.5
		#   = (row number + 0.5 / number of rows) - 0.5
		# y is the center of the element, image size scaled to 1.0, center at 0.0
		y = float(j) / float(ny) + resy

		# for each element (column) in the row in the image to be added
		for i in xrange(nx):

			# icnt is the flat index into the image to be added
#			icnt = j * nx + i

			# x = (column number / # of columns) + (1 / (2 * # of columns)) - 0.5
			#   = (row number + 0.5 / number of rows) - 0.5
			# x is the center of the element, image size scaled to 1.0, center at 0.0
			x = float(i) / float(nx) + resx

			# gx, gy are x,y rotated by theta
			# gx = x index scaled by theta + y index scaled by theta
			gx = x * costheta + y * sintheta
			# gy = y index scaled by theta - y index scaled by theta
			gy = x * sintheta - y * costheta

			# gx, gy scaled by sclx, scly and offset by gxoff, gyoff
			gx = nx * sclx * gx + gxoff
			gy = ny * scly * gy + gyoff

			# igx, igy are gx, gy scale to stage range and mosaic image size	
			igx = gnx * (gx - gxmin) / gxrnge
			igy = gny * (gy - gymin) / gyrnge

			# igcnt is the flat index into the mosaic image
#			igcnt = igy * gnx + igx

			# if the index is within the mosaic image bounds and element is greater
			# than the threshold then add it to the mosaic image
#			if (igcnt > 0) and (igcnt < gnpix) and (img[icnt] > thresh):
#				gimg[int(round(igcnt))] = img[icnt]
			# IndexError
			if img[j, i] > thresh:
				gimg[int(round(igy)), int(round(igx))] = img[j, i]

