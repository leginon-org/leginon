import math
import Numeric

def add_piece(target, source, gxoff, gyoff, theta, sclx, scly, thresh,
																						gxmin, gxmax, gymin, gymax):

	sintheta = math.sin(theta)			# sine of the source image angle
	costheta = math.cos(theta)			# cosine of the source image angle

	stagemin = Numeric.array([gymin, gxmin], Numeric.Float32)
	stagemax = Numeric.array([gymax, gxmax], Numeric.Float32)
	stagerange = stagemax - stagemin

	# pixel size/scale
	scale = Numeric.array([scly, sclx], Numeric.Float32)

	# rotation matrix for rotated vectors from stage to image coordinates
	rotation = Numeric.array([[-costheta, sintheta],
														[sintheta, costheta]], Numeric.Float32)

	# stage position
	sourceoffset = Numeric.array([gyoff, gxoff], Numeric.Float32)

	# stage units per pixel size of target image
	targetpixelperstage = target.shape / stagerange

	# stage coordinate offset in target image + stage coordinate offset of source
	totaloffset = -stagemin * targetpixelperstage \
				+ Numeric.matrixmultiply(rotation, sourceoffset * targetpixelperstage)

	roundedtotaloffset = (int(round(totaloffset[0])), int(round(totaloffset[1])))

	# stage units per pixel size of target image scaled by pixel size/scale
	scaledtargetpixelperstage = 1 / (scale * targetpixelperstage)

	# shape of image to be copied to target
	scaledsourceshape = source.shape / scaledtargetpixelperstage
	roundedscaledsourceshape = (int(round(scaledsourceshape[0])),
															int(round(scaledsourceshape[1])))

	# for each pixel in target that will be copied
	for i in range(roundedscaledsourceshape[0]):
		for j in range(roundedscaledsourceshape[1]):
			# set the target to the source image coordinate scaled
			# to size when added to the target
			target[roundedtotaloffset[0] + i, roundedtotaloffset[1] + j] = \
							source[int(round(i * scaledtargetpixelperstage[0])),
											int(round(j * scaledtargetpixelperstage[1]))]

