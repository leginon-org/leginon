function val = objenv(x,A,b)
%
% DESCRIPTION:  
%     Calculates the value objective function ||Ax-b||^2 .
%
% USAGE: 
%     val = obj(x,A,b)
%
% Copyright 2004-2005 Satya P. Mallick. 

val = norm((A*x-b),2);
%val = sqrt(sum((A*x-b).^2./A(:,4))/sum(1/A(:,4)));

