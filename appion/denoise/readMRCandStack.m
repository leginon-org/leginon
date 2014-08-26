function [stack rez] = readMRCandStack(x,na,start,nslice,roi)
% filename - mrc filename with path
% na - number of frames to average together in moving window
% start - frame to start on (first frame is 1)
% nslice - number oi frames total to include
% roi - [x1 y1 x2 y2] xy pairs of the top-left and bottom right corners

if nargin < 4
    roi = [1 1 inf inf];
end

if isa(x,'char')
    disp('Reading MRC')
    [map s]=ReadMRC(x,start,nslice);
    rez = s.rez;
  
elseif (isnumeric(x) && ndims(x)>1)
    map = x;
    rez = -inf;
    clear x;
end

startx = max([abs(roi(1)),1]);
starty = max([abs(roi(2)),1]);

stopx = min([abs(roi(3)),size(map,1)]);
stopy = min([abs(roi(4)),size(map,2)]);

rectx = int32(startx:stopx);
recty = int32(starty:stopy);
if ((size(map,3)-na)>1 && na > 1);
    for i = 1:(size(map,3)-na+1)
        st = i;
	% range is inclusive i.e.,(1:3) means (1,2,3)
        stack(:,:,i) = mean(double(map(rectx,recty,(st:st+na-1))),3);
    end
    
elseif (na == 1)
    stack = map(recty,rectx,start:end);
else
    stack = mean(double(map(recty,rectx,start:end)),3);
end
%stack = adjust(stack,1,3);

