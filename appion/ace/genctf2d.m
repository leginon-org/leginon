function onlyctf = genctf2d(imwidth,ctfparams,scopeparams) 
%
% DESCRIPTION: 
%     Generates the 2D CTF. 
%
% USAGE: 
%     ctf = genctf2d(imwidth, ctfparams,scopeparams) 
%
%     imwidth     : Width of the image. 
%     ctfparams   : Parameter vector of the CTF parameters. 
%     scopeparams : Parameter vector of microscope parameters. 
%     ctf         : The contrast transfer function. 
%
% Copyright 2004-2005 Satya P. Mallick 

defoci = ctfparams(1:2); 
A = ctfparams(3); 
ast_ang =  pi/2+ctfparams(4); 
noisep = ctfparams(5:8); 
envp = ctfparams(9:12); 

V = scopeparams(1)*1e3; 
Cs = scopeparams(2)*1e-3; 
Ca = scopeparams(3)*1e-10; 

if(mod(imwidth,2)==0)
 zro = imwidth/2+0.5; 
else 
  zro = ceil(imwidth/2) 
end 

defocus_mean = (defoci(1)+defoci(2))/2; 
defocus_dev = abs(defoci(1)-defoci(2))/2; 
lambda = getlambda(V);

[i,j] = meshgrid(1:imwidth); 

r = ((i-zro).^2 + (j-zro).^2).^(0.5); 
s = r./(imwidth*Ca);
ang = atan((j-zro)./(i-zro)); 
d = defocus_mean + defocus_dev*cos(2*(ang-ast_ang)); 
gmma = squeeze(getgamma(s,d,Cs,lambda)); 
env = exp(2*(envp(1)+envp(2).*s.^0.5 + envp(3).*s + envp(4).*s.^2)); 
noise = exp(2*(noisep(1)+ noisep(2).*s^0.5 + noisep(3).*s + noisep(4).*s.^2));
ctf = env.*(sqrt(1-A^2)*sin(gmma)+A*cos(gmma)).^2+noise;

onlyctf = (sqrt(1-A^2)*sin(gmma)+A*cos(gmma));
[indx1 indy1] = find(abs(gmma-pi)<0.04); 
save indx1 indx1
save indy1 indy1




 

