function [stackparams] = makeStackparams(na,start,nslice,roi);
% na - number of frames to average together in moving window
% start - frame to start on
% nslice - total number of frames to include
% roi - [x1 y1 x2 y2] xy pairs of the top-left and bottom right corners



if nargin < 3
    roi = [1 1 inf inf];
end

if nargin < 1
    start = 4;
    na = 8;
    nslice = start+na
end

stackparams.roi = roi;
stackparams.nslice = nslice;
stackparams.na = na;
stackparams.start = start;

end
