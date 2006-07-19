function saveeps(filename)
%SAVEEPS  : Saves current figure as an eps file. 
%
%Usage    : 
%          saveeps(filename)
h = gcf; 
saveas(h,filename,'epsc2'); 
