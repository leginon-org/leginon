import math
import Numeric

def add_piece(target, source, gxoff, gyoff, theta, sclx, scly, thresh,
																						gxmin, gxmax, gymin, gymax):

	sintheta = math.sin(theta)			# sine of the source image angle
	costheta = math.cos(theta)			# cosine of the source image angle

	stagemin = Numeric.array([gymin, gxmin], Numeric.Float32)
	stagemax = Numeric.array([gymax, gxmax], Numeric.Float32)
	stagerange = stagemax - stagemin

	scale = Numeric.array([scly, sclx], Numeric.Float32)

	rotation = Numeric.array([[-costheta, sintheta],
														[sintheta, costheta]], Numeric.Float32)

	sourceoffset = Numeric.array([gyoff, gxoff], Numeric.Float32)

	targetpixelperstage = target.shape / stagerange

	scaledtargetpixelperstage = scale * targetpixelperstage

	sourceoffset = sourceoffset * targetpixelperstage

	sourceoffset = Numeric.matrixmultiply(rotation, sourceoffset)

	targetoffset = (int(round(float(target.shape[0])/2.0)),
									int(round(float(target.shape[1])/2.0)))

	print sourceoffset

	for i in range(source.shape[0]):
		for j in range(source.shape[1]):
			stagerow = targetoffset[0] + int(round(sourceoffset[0]
																				+ i*scaledtargetpixelperstage[0]))
			stagecolumn = targetoffset[1] + int(round(sourceoffset[1]
																				+ j*scaledtargetpixelperstage[1]))
			target[stagerow, stagecolumn] = source[i, j]

