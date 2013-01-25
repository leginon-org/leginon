function [ksvdparams] = makeKSVDparams(blocksize,dictsize,sigma)
% blocksize : size of KSVD atom blocks (8)
% dictsize : length of dictionary (64)
% sigma : sigma value used in denoising (1/400)

if nargin < 1
    blocksize = 8;
    dictsize = 64;
    sigma = 10;
end
ksvdparams.blocksize = blocksize;
ksvdparams.dictsize = dictsize;
ksvdparams.sigma = sigma;
ksvdparams.trainnum = 40000;
ksvdparams.memusage = 'high';


end