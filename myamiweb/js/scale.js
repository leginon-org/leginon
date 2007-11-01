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

function findScale(imgsize, pixelsize) {
	nbpixels=1
	for (var key in scales) {
		scale=scales[key]
		nbpixels = scale/pixelsize
		r = imgsize/nbpixels;
		if (r > 2 && r <5) {
			break;
		}
	}
	return new Array(parseInt(nbpixels),key)
}
