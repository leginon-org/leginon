function autofocus(scopeaddr, camaddr, tilt, defocus)
win = figure(1);
set(win,'Name','emMatlab Autofocus Demo','NumberTitle','off');
axis('off');
figure(1);
subplot(4,4,1);

savedefocus = emMatlab(scopeaddr, 'get', 'defocus');
shift1 = getpixelshift(scopeaddr, camaddr, tilt, 1);
emMatlab(scopeaddr, 'set', 'defocus', savedefocus - defocus);
shift2 = getpixelshift(scopeaddr, camaddr, tilt, 2);
emMatlab(scopeaddr, 'set', 'defocus', savedefocus);

calx = (shift2(1) - shift1(1))/ defocus;
caly = (shift2(2) - shift1(2))/ defocus;

% not really necessary
shift = getpixelshift(scopeaddr, camaddr, tilt, 3);

deltadefocus = (shift(1)/calx + shift(2)/caly)/2
emMatlab(scopeaddr, 'set', 'defocus', savedefocus - deltadefocus);

finalshift = getpixelshift(scopeaddr, camaddr, tilt, 4);
