function shift = getpixelshift(scopeaddr, camaddr, delta, n)
beamtilt = emMatlab('http://amilab8:8000', 'get', 'beam tilt');

nbeamtilt = [beamtilt(1) - delta/2 beamtilt(2)];
emMatlab('http://amilab8:8000', 'set', 'beam tilt', nbeamtilt);
image1 = emMatlab('http://amilab8:8001', 'get', 'image data');
displayimage(image1, 4*n-3);

nbeamtilt = [beamtilt(1) + delta beamtilt(2)];
emMatlab('http://amilab8:8000', 'set', 'beam tilt', nbeamtilt);
image2 = emMatlab('http://amilab8:8001', 'get', 'image data');
displayimage(image1, 4*n-2);

emMatlab('http://amilab8:8000', 'set', 'beam tilt', beamtilt);

shift = phasecorrelation(image1, image2, 4*n-1);
imageoverlap(image1, image2, shift, 4*n);
