function displayimage(im, n)
subplot(4,4,n);
set(subplot(4,4,n), 'XTickMode', 'manual', 'YTickMode', 'manual');
set(subplot(4,4,n), 'XTick', [], 'YTick', []);
subimage(im, [0 2000]);
