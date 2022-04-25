import math
import os
import sys
import numpy
import random
import time
import pprint
from appionlib import apDisplay

#==================
#==================
#==================
def degreesToRadians(d):
	return d*math.pi/180

#==================	
def radiansToDegrees(r):
	return r*180/math.pi

#==================
def convert3DEMEulerToStandardSym(full_sym_name,phi,theta,omega):
	'''
	convert 3DEM Eulers applied to given volume at any orientation convention of any symmetry to create a projection view
	to eulers for the same volume oriented in the orientation convention in Appion database that would give the same projection view if applied with the package that Appion database orientation convention assumed.
	'''
	if 'Icos' not in full_sym_name:
		return phi,theta,omega
	else:
		'''
		Current Appion Icos Eulers are saved as that need to be applied to 532 (EMAN) orientation.
		'''
		return convert3DEMIcosEulerTo532(full_sym_name,phi,theta,omega)

#==================
def convert3DEMIcosEulerTo532(full_sym_name,phi,theta,omega):
	if 'Icos' not in full_sym_name:
		return phi,theta,omega
	r_in = EulersToRotationMatrix3DEM(phi, theta, omega)
	i_matrix = numpy.matrix([[1,0,0],[0,1,0],[0,0,1]])
	if '3DEM' in full_sym_name:
		# (235) to (253)
		symr1 = EulersToRotationMatrix3DEM(90,0,0)
	else:
		symr1 = i_matrix
	if 'EMAN' not in full_sym_name:
		# (253) to (532)
		symr2 = EulersToRotationMatrix3DEM(-90,90,-31.7174744)
	else:
		symr2 = i_matrix
	symr = symr1 * symr2
	r_out = r_in * symr
	phi,theta,omega = rotationMatrixToEulers3DEM(r_out)
	return phi,theta,omega

#==================
def convert3DEMEulerFromStandardSym(full_sym_name,phi,theta,omega):
	'''
	convert to 3DEM Eulers of volume at orientation convention of any symmetry 
	from  eulers for the same volume oriented in the orientation convention in Appion database.
	'''
	if 'Icos' not in full_sym_name:
		return phi,theta,omega
	else:
		'''
		Current Appion Icos Eulers are saved as that need to be applied to 532 (EMAN) orientation.
		'''
		return convert3DEMIcosEulerFrom532(full_sym_name,phi,theta,omega)

#==================
def convert3DEMIcosEulerFrom532(full_sym_name,phi,theta,omega):
	if 'Icos' not in full_sym_name:
		return phi,theta,omega
	r_in = EulersToRotationMatrix3DEM(phi, theta, omega)
	i_matrix = numpy.matrix([[1,0,0],[0,1,0],[0,0,1]])
	'''
	Euler conversion runs the opposite direction of model rotation
	'''
	if 'EMAN' not in full_sym_name:
		# inverse of (253) to (532)
		symr1 = EulersToRotationMatrix3DEM(-90,90,-31.7174744).I
	else:
		symr1 = i_matrix
	if '3DEM' in full_sym_name:
		# inverse of (235) to (253)
		symr2 = EulersToRotationMatrix3DEM(90,0,0).I
	else:
		symr2 = i_matrix
	symr = symr1 * symr2
	r_out = r_in * symr
	phi,theta,omega = rotationMatrixToEulers3DEM(r_out)
	return phi,theta,omega

#==================
def convert3DEMEulers(phi,theta,omega,phi_r,theta_r,omega_r):
	''' HAS NOT BEE TESTED '''
	m_in = EulersToRotationMatrix3DEM(phi, theta, omega)
	m_in_rotate = EulersToRotationMatrix3DEM(phi_r, theta_r, omega_r)
	m_out = m_in * m_in_rotate
	phi,theta,omega = rotationMatrixToEulers3DEM(m_out)
	return phi,theta,omega
			
#==================
def EulersToRotationMatrixEMAN(alt, az, phi, mirror=False):
	''' 
	this code was taken from the Transform class in Sparx and EMAN2 
	http://blake.bcm.edu/eman2/doxygen_html/transform_8cpp_source.html#l00511	
	'''
#	return getEmanEulerMatrix({'euler1':alt, 'euler2':az}, phi)
	if mirror == True:
		alt, az, phi = calculate_equivalent_EMANEulers_without_flip(alt, az, phi)

	alt = degreesToRadians(alt)
	az = degreesToRadians(az)
	phi = degreesToRadians(phi)
	
	m = numpy.zeros((3,3), dtype=numpy.float32)
	m[0][0] = math.cos(phi)*math.cos(az) - math.cos(alt)*math.sin(az)*math.sin(phi)
	m[0][1] = math.cos(phi)*math.sin(az) + math.cos(alt)*math.cos(az)*math.sin(phi)
	m[0][2] = math.sin(alt)*math.sin(phi)
	m[1][0] = -math.sin(phi)*math.cos(az) - math.cos(alt)*math.sin(az)*math.cos(phi)
	m[1][1] = -math.sin(phi)*math.sin(az) + math.cos(alt)*math.cos(az)*math.cos(phi)
	m[1][2] = math.sin(alt)*math.cos(phi)
	m[2][0] = math.sin(alt)*math.sin(az)
	m[2][1] = -math.sin(alt)*math.cos(az)
	m[2][2] = math.cos(alt)

	return numpy.matrix(m)
	
#==================	
def EulersToRotationMatrix3DEM(phi, theta, omega):
	'''
	phi in degrees, theta in degrees, omega in degrees; takes Euler angles as rotation, tilt, and omega (in degrees) and 
	converts to a 3x3 rotation matrix, according to ZYZ convention.
	'''

	phi = degreesToRadians(phi)
	theta = degreesToRadians(theta)
	omega = degreesToRadians(omega)

	m = numpy.zeros((3,3), dtype=numpy.float32)
	m[0][0] = math.cos(omega)*math.cos(theta)*math.cos(phi) - math.sin(omega)*math.sin(phi)
	m[0][1] = math.cos(omega)*math.cos(theta)*math.sin(phi) + math.sin(omega)*math.cos(phi)
	m[0][2] = -math.cos(omega)*math.sin(theta)
	m[1][0] = -math.sin(omega)*math.cos(theta)*math.cos(phi) - math.cos(omega)*math.sin(phi)
	m[1][1] = -math.sin(omega)*math.cos(theta)*math.sin(phi) + math.cos(omega)*math.cos(phi)
	m[1][2] = math.sin(omega)*math.sin(theta)
	m[2][0] = math.sin(theta)*math.cos(phi)
	m[2][1] = math.sin(theta)*math.sin(phi)
	m[2][2] = math.cos(theta)

	### round off any values close to 0, default set to 0.001
	default = 0.000001
	m = numpy.where(abs(m) < default, 0, m)
	return numpy.matrix(m)

#==================
def EulersToRotationMatrixXmipp(phi, theta, psi):
	return EulersToRotationMatrix3DEM(phi, theta, psi) 

#==================
def EulersToRotationMatrixSPIDER(phi, theta, psi):
	return EulersToRotationMatrix3DEM(phi, theta, psi)

#==================
def rotationMatrixToEulersEMAN(m):
	''' 
	this code was taken from the Transform class in Sparx and EMAN2 
	http://blake.bcm.edu/eman2/doxygen_html/transform_8cpp_source.html#l00511
	The input matrix must has no mirror.  The original code is different
	when mirror (flip x) is present.
	'''

	if type(m) is not numpy.ndarray:
		m = numpy.asarray(m)

	### round off any values close to 0, default set to 0.00001 to fit case
	default = 0.000001
	m = numpy.where(abs(m) < default, 0, m)

	cosalt = m[2][2]
	if cosalt >= 1:
		alt = 0
		az = 0
		phi = radiansToDegrees(math.atan2(m[0][1], m[0][0]))
	elif cosalt <= -1:
		alt = 180
		az = 0
		phi = radiansToDegrees(math.atan2(-m[0][1], m[0][0]))
	else:
		az = radiansToDegrees(math.atan2(m[2][0], -m[2][1]))
		if m[2][2] == 0:
			alt = 90.0
		else:
			alt = radiansToDegrees(math.atan(math.sqrt(m[2][0]*m[2][0]+m[2][1]*m[2][1])/abs(m[2][2])))
		
		if m[2][2] < 0:
			alt = 180.0 - alt
		phi = radiansToDegrees(math.atan2(m[0][2], m[1][2]))

	phi = phi - 360.0 * math.floor(phi / 360.0)
	az = az - 360.0 * math.floor(az / 360.0)

	return alt, az, phi

#==================
def rotationMatrixToEulers3DEM(m):
	'''
	matrix as a numpy array; recovers Euler angles in degrees from 3x3 rotation matrix or array. Procedure assumes that the tilt
	Euler angle is < 180, i.e. pi. This follows the ZYZ convention of 3DEM with a standard coordinate system 
	'''

	if type(m) is not numpy.ndarray:
		m = numpy.asarray(m)
		
	### round off any values close to 0, default set to 0.001
	default = 0.000001
	m = numpy.where(abs(m) < default, 0, m)

	theta = math.acos(m[2][2])
	if theta > 0 and theta < math.pi: 		
		phi = math.atan2(m[2][1], m[2][0])
		if m[0][2] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
			omega = math.atan2(m[1][2], m[0][2])
		else:
			omega = math.atan2(m[1][2], -m[0][2])
	elif round(theta,4) == round(0,4):
		phi = 0
		if m[1][0] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
			omega = math.atan2(m[1][0], m[0][0])
		else:
			omega = math.atan2(-m[1][0], m[0][0])
	elif round(theta,4) == round(math.pi,4):
		phi = 0
		if m[0][0] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
			omega = math.atan2(m[1][0], m[0][0])
		else:
			omega = math.atan2(m[1][0], -m[0][0])
	else:
		phi = 0
		if m[1][0] == 0: ### atan2(0.0,-0.0) returns 180, but we need 0
			omega = math.atan2(m[1][0], m[0][0])
		else:
			omega = math.atan2(-m[1][0], m[0][0])
	phi = radiansToDegrees(phi)
	theta = radiansToDegrees(theta)
	omega = radiansToDegrees(omega)

	return phi, theta, omega

#==================
def rotationMatrixToEulersXmipp(m):
	return rotationMatrixToEulers3DEM(m)

#==================
def rotationMatrixToEulersSPIDER(m):
	return rotationMatrixToEulers3DEM(m)

#==================
def calculate_equivalent_EMANEulers_without_flip(alt, az, phi):
	''' takes transform matrix, multiplies by mirror_matrix, inverses sign of psi '''

	m = numpy.matrix(EulersToRotationMatrixEMAN(alt, az, phi))
	mmirror = numpy.matrix([[-1,0,0],[0,-1,0],[0,0,-1]])
	mnew = m * mmirror
	newalt, newaz, newphi = rotationMatrixToEulersEMAN(mnew)
	### this was assessed empirically, works on synthetic data projected with project3d
	newphi = newphi + 180
	return newalt, newaz, newphi

#==================
def calculate_equivalent_XmippEulers_without_flip(phi, theta, psi):
	''' takes transform matrix, multiplies by mirror_matrix, inverses sign of psi '''
	m = EulersToRotationMatrixXmipp(phi, theta, psi)
	mmirror = numpy.matrix([[-1,0,0],[0,-1,0],[0,0,-1]])
	mnew = m * mmirror
	newphi, newtheta, newpsi = rotationMatrixToEulersXmipp(mnew)
	### this was assessed empirically, works on synthetic data projected with xmipp_project
	newpsi = -newpsi
	return newphi, newtheta, newpsi
#======================================= 		Euler Angle Conversions			  =========================

def convertXmippEulersToEman(phi, theta, psi,mirror=False):
	''' 
	converts Xmipp / Spider Euler angles to EMAN, according to:
	Baldwin, P.R., and Penczek, P.A. (2007). The Transform Class in SPARX and EMAN2. Journal of Structural Biology 157, 250-261.
	also see for reference:
	http://blake.bcm.edu/eman2/doxygen_html/transform_8cpp_source.html
	http://blake.bcm.edu/emanwiki/Eman2TransformInPython
	'''
	# mirror in Xmipp and Eman are not oriented in the same way, therefore, the flip needs to be done first
	if mirror:
		phi,theta,psi = calculate_equivalent_XmippEulers_without_flip(phi, theta, psi)
	az = math.fmod((phi+90),360.0)
	alt = math.fmod(theta,360.0)
	phi = math.fmod((psi-90),360.0)
	# This Eman result should not contain mirror
	return alt, az, phi

#===================
def convertEmanEulersToXmipp(alt, az, psi):
	''' reverse of convertXmippEulersToEman '''
	phi = math.fmod((az-90), 360.0)
	theta = math.fmod(alt,360.0)
	psi = math.fmod((psi+90), 360.0)
	return phi, theta, psi

#==================
def convertXmippEulersToFrealign(phi, theta, psi):
	'''
	verified empirically using a reconstruction from 100,000 particles generated using Frealign with the converted Eulers.
	These angle conversions give identical volumes using Xmipp & Frealign 
	'''
	phi = math.fmod(phi,360.0)
	theta = math.fmod(theta,360.0)
	psi = math.fmod(psi,360.0)
	return phi, theta, psi

#==================
def convert3DEMEulersToFrealign(phi, theta, omega):
	'''
	Same as convertXmippEulersToFrealign
	'''
	return convertXmippEulersToFrealign(phi, theta, omega)

#==================
def convertFrealignEulersToXmipp(phi, theta, psi):
	''' reverse of convertXmippEulersToFrealign '''
	phi = math.fmod(phi,360.0)
	theta = math.fmod(theta,360.0)
	psi = math.fmod(psi,360.0)
	return phi, theta, psi 

#==================
def convertFrealignEulersTo3DEM(phi, theta, psi):
	''' reverse of convert3DEMEulersToFrealign.
	Output normally named, in order, phi, theta, omega
	'''
	return convertFrealignEulersToXmipp(phi, theta, psi)

#======================================			Rest of Functions			==========================

#==================
def eulerCalculateDistance(e1, e2, inplane=False):
	"""
	given two euler as dicts
	calculate distance between euler values
	value in degrees
	"""
	mat0 = getEmanEulerMatrix(e1, inplane=inplane)
	mat1 = getEmanEulerMatrix(e2, inplane=inplane)
	dist = computeDistance(mat0, mat1)
	#convert to degrees
	return dist

#==================
def eulerCalculateDistanceSym(e1, e2, sym='d7', inplane=False):
	"""
	given two euler as dicts in degrees
	calculate distance between euler values
	value in degrees

	euler1 = alt
	euler2 = az
	euler3 = in plane rotation
	"""
	e1mat = getEmanEulerMatrix(e1, inplane=inplane)
	#print e1mat
	#get list of equivalent euler matrices
	if len(sym) > 3 and sym.lower()[:4] == "icos":
		e2equivMats = calculateEquivIcos(e2, inplane=inplane)
	else:
		e2equivMats = calculateEquivSym(e2, sym=sym, inplane=inplane)
	#print e2equivMats[0]

	# calculate the distances between the original Euler and all the equivalents
	mindist = 360.0
	distlist = []
	for e2mat in e2equivMats:
		dist = computeDistance(e1mat, e2mat)
		distlist.append(dist)
		if dist < mindist:
			mindist = dist
	"""
	if mindist > 91.0:
		print round(mindist,4),"<--",numpy.around(distlist,2)
		pprint.pprint(e1)
		pprint.pprint(e2)
		print ""
	"""

	#convert to degrees
	return mindist

#==================
def calculateEquivSym(euler, sym='d7', symout=False, inplane=False):
	"""
	rotates eulers about any c and d symmetry group

	input:
		individual euler dict
	output:
		list of equiv. euler matrices
	"""
	symMats = []

	# calculate each of the rotations around z axis
	numrot = int(sym[1:])
	for i in range(numrot):
		symMats.append( calcZRot(2.0*math.pi*float(i)/float(numrot)) )

	# if D symmetry, combine each rotations with x axis rotation
	if sym[0] == 'd':
		x1 = calcYRot(math.pi)
		for i in range(numrot):
			symMats.append( numpy.dot(x1, symMats[i]) )

	#calculate new euler matices
	eulerMat = getEmanEulerMatrix(euler, inplane=inplane)
	equivMats=[]
	for symMat in symMats:
		equivMats.append(numpy.dot(eulerMat, symMat))

	if symout is True:
		f=open('matrices.txt','w')
		for n,e in enumerate(equivMats):
			f.write('REMARK 290    SMTRY1  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[0,0], e[0,1], e[0,2]))
			f.write('REMARK 290    SMTRY2  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[1,0], e[1,1], e[1,2]))
			f.write('REMARK 290    SMTRY3  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[2,0], e[2,1], e[2,2]))
		f.close()
	return equivMats

#==================
def calculateEquivIcos(euler, symout=False, inplane=False):
	"""
	rotates eulers about icosahedral symmetry group

	input:
		individual euler dict
	output:
		list of equiv. euler matrices
	"""
	symMats = []

	### first 5 rotations
	for i in range(5):
		symMats.append( calcZRot(2.0*math.pi*float(i)/float(5)) )
	### second 5 are rotated 180 out of phase
	x1 = calcYRot(math.pi)
	for i in range(5):
		symMats.append( numpy.dot(x1, symMats[i]) )
	### next 25 include a y rotation duplicated 5 times with another z rotation
	y1 = calcYRot(296.56505*math.pi/180.0)
	for i in range(5):
		mysym = numpy.dot(y1, calcZRot(2.0*math.pi*float(i)/5.0+36.0))
		symMats.append( mysym )
		for i in range(4):
			z2 = calcZRot(2.0*math.pi*float(i+1)/5.0)
			symMats.append( numpy.dot(z2, mysym) )
	### final 25 include a y rotation duplicated 5 times with another z rotation
	y1 = calcYRot(243.43495*math.pi/180.0)
	for i in range(5):
		mysym = numpy.dot(y1, calcZRot(2.0*math.pi*float(i)/5.0))
		symMats.append( mysym )
		for i in range(4):
			z2 = calcZRot(2.0*math.pi*float(i+1)/5.0+36.0)
			symMats.append( numpy.dot(z2, mysym) )

	#calculate new euler matices
	eulerMat = getEmanEulerMatrix(euler, inplane=inplane)
	equivMats=[]
	for symMat in symMats:
		equivMats.append(numpy.dot(eulerMat, symMat))

	if symout is True:
		f=open('matrices.txt','w')
		for n,e in enumerate(equivMats):
			f.write('REMARK 290    SMTRY1  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[0,0], e[0,1], e[0,2]))
			f.write('REMARK 290    SMTRY2  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[1,0], e[1,1], e[1,2]))
			f.write('REMARK 290    SMTRY3  %2d   %5.2f %5.2f %5.2f     0.0\n' % (n+1, e[2,0], e[2,1], e[2,2]))
		f.close()
	return equivMats

#==================
def getEmanEulerMatrix(eulerdata, inplane=True):
	return getMatrix3(eulerdata, inplane=inplane)

#==================
def getMatrix(eulerdata):
	a=eulerdata['euler3']*math.pi/180
	b=eulerdata['euler1']*math.pi/180
	c=eulerdata['euler2']*math.pi/180
	m=numpy.zeros((3,3))
	m[0,0]=math.cos(c)*math.cos(a)-math.cos(b)*math.sin(a)*math.sin(c)
	m[0,1]=math.cos(c)*math.sin(a)+math.cos(b)*math.cos(a)*math.sin(c)
	m[0,2]=math.sin(c)*math.sin(b)
	m[1,0]=-math.sin(c)*math.cos(a)-math.cos(b)*math.sin(a)*math.cos(c)
	m[1,1]=-math.sin(c)*math.sin(a)+math.cos(b)*math.cos(a)*math.cos(c)
	m[1,2]=math.cos(c)*math.sin(b)
	m[2,0]=math.sin(b)*math.sin(a)
	m[2,1]=-math.sin(b)*math.cos(a)
	m[2,2]=math.cos(b)
	return m

#==================
def getMatrix2(eulerdata):
	alpha=eulerdata['euler1']*math.pi/180
	beta=eulerdata['euler2']*math.pi/180
	gamma=eulerdata['euler3']*math.pi/180

	alpham=numpy.zeros((3,3))
	betam=numpy.zeros((3,3))
	gammam=numpy.zeros((3,3))

	gammam[0,0]=math.cos(gamma)
	gammam[0,1]=math.sin(gamma)
	gammam[1,0]=-math.sin(gamma)
	gammam[1,1]=math.cos(gamma)
	gammam[2,2]=1.0

	betam[0,0]=1.0
	betam[1,1]=math.cos(beta)
	betam[1,2]=math.sin(beta)
	betam[2,1]=-math.sin(beta)
	betam[2,2]=math.cos(beta)

	alpham[0,0]=math.cos(alpha)
	alpham[0,1]=math.sin(alpha)
	alpham[1,0]=-math.sin(alpha)
	alpham[1,1]=math.cos(alpha)
	alpham[2,2]=1.0

	m=numpy.dot(gammam,betam)
	m=numpy.dot(m,alpham)
	m2=numpy.dot(alpham,betam)
	m2=numpy.dot(m2,gammam)

	return(m)

#==================
def getMatrix3(eulerdata, inplane=False):
	"""
	math from http://mathworld.wolfram.com/EulerAngles.html
	EMAN conventions - could use more testing
	tested by independently rotating object with EMAN eulers and with the
	matrix that results from this function
	"""
	#theta is a rotation about the x-axis, i.e. latitude
	# 0 <= theta <= 180 degrees
	the = eulerdata['euler1']*math.pi/180.0 #eman alt, altitude
	#phi is a rotation in the xy-plane, i.e. longitude
	# 0 <= phi <= 360 degrees
	phi = eulerdata['euler2']*math.pi/180.0 #eman az, azimuthal
	if inplane is True:
		psi = eulerdata['euler3']*math.pi/180.0 #eman phi, inplane_rotation
	else:
		psi = 0.0

	if 'mirror' in eulerdata and eulerdata['mirror'] == 1:
		"""
		using mirror function
		see: http://blake.bcm.tmc.edu/emanwiki/EMAN2/Symmetry
		for documentation
		"""
		#theta flips to the back
		the = math.pi - the
		#phi is rotated 180 degrees
		phi += math.pi
		#this works without in_plane
		if inplane is False:
			#psi is rotated 180 degrees
			psi += math.pi

	m = numpy.zeros((3,3), dtype=numpy.float32)
	m[0,0] =  math.cos(psi)*math.cos(phi) - math.cos(the)*math.sin(phi)*math.sin(psi)
	m[0,1] =  math.cos(psi)*math.sin(phi) + math.cos(the)*math.cos(phi)*math.sin(psi)
	m[0,2] =  math.sin(psi)*math.sin(the)
	m[1,0] = -math.sin(psi)*math.cos(phi) - math.cos(the)*math.sin(phi)*math.cos(psi)
	m[1,1] = -math.sin(psi)*math.sin(phi) + math.cos(the)*math.cos(phi)*math.cos(psi)
	m[1,2] =  math.cos(psi)*math.sin(the)
	m[2,0] =  math.sin(the)*math.sin(phi)
	m[2,1] = -math.sin(the)*math.cos(phi)
	m[2,2] =  math.cos(the)
	return m

#==================
def computeDistance(m1,m2):
	r = numpy.dot(m1.transpose(),m2)
	#print r
	trace = r.trace()
	s = (trace-1.0)/2.0
	if int(round(abs(s),7)) == 1:
		"""
		Either:
		 (1) Vectors are the same , i.e. 0 degrees
		 (2) Vectors are opposite, i.e. 180 degrees
		"""
		diff = numpy.sum(pow((m1-m2),2))
		#apDisplay.printWarning("overflow return, diff="+str(diff)+" m1="+str(m1)+" m2="+str(m2))
		if diff < 1.0e-6:
			return 0.0
		return 180.0
	else:
		#print "calculating"
		theta = math.acos(s)
		#print 'theta',theta
		t1 = abs(theta/(2*math.sin(theta)))
		#print 't1',t1
		t2 = math.sqrt(pow(r[0,1]-r[1,0],2)+pow(r[0,2]-r[2,0],2)+pow(r[1,2]-r[2,1],2))
		#print 't2',t2, t2*180/math.pi
		dist = t1 * t2
		dist *= 180.0/math.pi
		#print 'dist=',dist
		return dist

#==================
def calcXRot(a):
	m=numpy.zeros((3,3))
	m[0,0]=1
	m[0,1]=0
	m[0,2]=0
	m[1,0]=0
	m[1,1]=math.cos(a)
	m[1,2]=-(math.sin(a))
	m[2,0]=0
	m[2,1]=math.sin(a)
	m[2,2]=math.cos(a)
	return m

#==================
def calcYRot(a):
	m=numpy.zeros((3,3))
	m[0,0]=math.cos(a)
	m[0,1]=0
	m[0,2]=math.sin(a)
	m[1,0]=0
	m[1,1]=1
	m[1,2]=0
	m[2,0]=-(math.sin(a))
	m[2,1]=0
	m[2,2]=math.cos(a)
	return m

#==================
def calcZRot(a):
	m=numpy.zeros((3,3))
	m[0,0]=math.cos(a)
	m[0,1]=-(math.sin(a))
	m[0,2]=0
	m[1,0]=math.sin(a)
	m[1,1]=math.cos(a)
	m[1,2]=0
	m[2,0]=0
	m[2,1]=0
	m[2,2]=1
	return m

#==================
def henryMult(m1,m2):
	c=numpy.zeros((m1.shape[0],m2.shape[1]))
	for i in range(0,c.shape[0]):
		for j in range(0,c.shape[1]):
			tot=0
			for k in range(0,m1.shape[1]):
				tot+=m1[i,k]*m2[k,j]
			c[i,j]=tot
	return c


