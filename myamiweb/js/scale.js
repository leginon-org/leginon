var scales={
	'1nm' : 1e-9,
	'2nm' : 2e-9,
	'5nm' : 5e-9,
	'10nm' : 10e-9,
	'20nm' : 20e-9,
	'50nm' : 50e-9,
	'100nm' : 100e-9,
	'200nm' : 200e-9,
	'500nm' : 500e-9,
	'1um' : 1e-6,
	'2um' : 2e-6,
	'5um' : 5e-6,
	'10um' : 10e-6,
	'20um' : 20e-6,
	'50um' : 50e-6,
	'100um' : 100e-6,
	'200um' : 200e-6,
	'500um' : 500e-6,
	'1mm' : 1e-3,
	'2mm' : 2e-3,
	'5mm' : 5e-3
}

var inverse_scales = {
	'1/1&Aring;': 1e-10,
	'1/2&Aring;'  : 2e-10,
	'1/4&Aring;'  : 4e-10,
	'1/7&Aring;'  : 7e-10,
	'1/1nm'  : 1e-9,
	'1/2nm'  : 2e-9,
	'1/4nm'  : 4e-9,
	'1/7nm'  : 7e-9,
	'1/10nm'  : 10e-9,
	'1/20nm'  : 20e-9,
	'1/40nm'  : 40e-9,
	'1/70nm'  : 70e-9,
	'1/100nm'  : 100e-9,
	'1/200nm'  : 200e-9,
	'1/400nm'  : 400e-9,
	'1/700nm'  : 700e-9,
	'1/1um'  : 1e-6,
	'1/2um'  : 2e-6,
	'1/4um'  : 4e-6,
	'1/7um'  : 7e-6,
	'1/10um' : 10e-6,
	'1/20um' : 20e-6,
	'1/40um' : 40e-6,
	'1/70um' : 70e-6,
	'1/100um' : 100e-6,
	'1/200um' : 200e-6,
	'1/400um' : 400e-6,
	'1/700um' : 700e-6,
	'1/1mm' : 1e-3,
	'1/2mm' : 2e-3,
	'1/4mm' : 4e-3,
	'1/7mm' : 7e-3
}
	
function findScale(imgsize, pixelsize) {
	nbpixels=1
	if (pixelsize < 1) {
		for (var key in scales) {
			scale=scales[key]
			nbpixels = scale/pixelsize
			r = imgsize/nbpixels;
			if (r > 2 && r <5) {
				break;
			}
		}
	} else {
		// Fourier space scale
		for (var key in inverse_scales) {
			scale=inverse_scales[key]
			nbpixels = 1/(scale * pixelsize)
			r = imgsize/nbpixels;
			if (r > 4 && r <8) {
				break;
			}
		}
	}
	return new Array(parseInt(nbpixels),key)
}
