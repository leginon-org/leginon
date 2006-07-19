function val = objnoise(x,A,b)
% DESCRIPTION: 
%     Calculates the value objective function ||Ax-b||^2
%
% USAGE: 
%     val = obj(x,A,b)
% 
% Copyright 2004-2005 Satya P. Mallick. 

bhat =  ones(length(b),1); 
l = length(bhat); 
bhat(round(l/2):end)=0;
val = norm((A*x-b).*bhat,1);

%val = sqrt(sum((A*x-b).^2./A(:,4))/sum(1/A(:,4)));

