%
% COPYRIGHT:
%       The Leginon software is Copyright 2003
%       The Scripps Research Institute, La Jolla, CA
%       For terms of the license agreement
%       see  http://ami.scripps.edu/software/leginon-license
%
function displayimage(im, n)
subplot(4,4,n);
set(subplot(4,4,n), 'XTickMode', 'manual', 'YTickMode', 'manual');
set(subplot(4,4,n), 'XTick', [], 'YTick', []);
subimage(im, [0 2000]);
