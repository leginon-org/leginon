%
% COPYRIGHT:
%       The Leginon software is Copyright 2003
%       The Scripps Research Institute, La Jolla, CA
%       For terms of the license agreement
%       see  http://ami.scripps.edu/software/leginon-license
%
function imageoverlap(im1, im2, shift, n)
shift = round(shift);
dim1 = size(im1);
dim2 = size(im2);
im = zeros(dim1 + abs(dim1 - dim2) + shift);

if shift(1) >= 0
    i1 = 1;
    i2 = shift(1);
else
    i1 = shift(1);
    i2 = 1;
end

if shift(2) >= 0
    j1 = 1;
    j2 = shift(2);
else
    j1 = shift(2);
    j2 = 1;
end

im(i1:i1+dim1(1)-1, j1:j1+dim1(2)-1) = im1;
im(i2:i2+dim2(1)-1, j2:j2+dim2(2)-1) = im2;

displayimage(im, n);
