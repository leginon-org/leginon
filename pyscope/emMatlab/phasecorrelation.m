function shift = phasecorrelation(im1, im2, n)
imdim = size(im1);
imcenter = imdim/2;
im1fft = double(fft2(im1));
im2fft = double(fft2(im2));
% ccfft = conj(im1fft) .* im2fft ./ sqrt( (im1fft + im2fft) .* conj(im1fft + im2fft));
ccfft = conj(im1fft).* im2fft ./ abs(conj(im1fft) .* im2fft);
cc = real(ifft2(ccfft));

centercc = cc(imcenter(1)+1:imdim(1),imcenter(2)+1:imdim(2));
centercc(imcenter(1)+1:imdim(1), 1:imcenter(2)) = cc(1:imcenter(1),imcenter(2)+1:imdim(2));
centercc(1:imcenter(1),imcenter(2)+1:imdim(2)) = cc(imcenter(1)+1:imdim(1), 1:imcenter(2));
centercc(imcenter(1)+1:imdim(1),imcenter(2)+1:imdim(2)) = cc(1:imcenter(1), 1:imcenter(2));
subplot(4,4,n);
surf(centercc);

max = 0;
maxcoord = [1 1];
% fit needs 2 pixel padding
for i = 3:imdim(1)-2,
  for j = 3:imdim(2)-2,
    if centercc(i,j) > max
      max = centercc(i,j);
      maxcoord = [i j];
    end
  end
end

xshift = (7.0/20.0) * (2.0*centercc(maxcoord(1) - 2, maxcoord(2)) + centercc(maxcoord(1) - 1, maxcoord(2)) -  centercc(maxcoord(1) + 1, maxcoord(2)) - 2.0*centercc(maxcoord(1) + 2, maxcoord(2))) / (2.0*centercc(maxcoord(1) - 2, maxcoord(2)) - centercc(maxcoord(1) - 1, maxcoord(2)) - 2.0*centercc(maxcoord(1), maxcoord(2)) -  centercc(maxcoord(1) + 1, maxcoord(2)) + 2.0*centercc(maxcoord(1) + 2, maxcoord(2)));

yshift = (7.0/20.0) * (2.0*centercc(maxcoord(1), maxcoord(2) - 2) + centercc(maxcoord(1), maxcoord(2) - 1) -  centercc(maxcoord(1), maxcoord(2) + 1) - 2.0*centercc(maxcoord(1), maxcoord(2) + 2)) / (2.0*centercc(maxcoord(1), maxcoord(2) - 2) - centercc(maxcoord(1), maxcoord(2) - 1) - 2.0*centercc(maxcoord(1), maxcoord(2)) -  centercc(maxcoord(1), maxcoord(2) + 1) + 2.0*centercc(maxcoord(1), maxcoord(2) + 2));

shift = [(xshift + maxcoord(1)) (yshift + maxcoord(2))];
