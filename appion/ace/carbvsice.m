%dirname = '/ami/data05/leginon/04jul20a/extract/ctf/04jul20a/';
dirname = '/ami/data04/spmallick/ctf/04apr14b/'; % directory
list = dir(strcat(dirname,'matfiles_foc1/*.mat')); 
k=0; 
l=0; 
figure;
hold on; 
for i=1:length(list) 
  
  load(strcat(dirname,'matfiles_foc1/',list(i).name));
  if(ctfparams~=-1) 
    if(abs(ctfparams(1)-abs(dforig))<1e-6)
      dfcarbon = ctfparams(1); 
      newlist = dir(strcat(dirname,'matfiles1/',list(i).name(1:end-16 ),'*3e*.mat')); 
      for(j=1:length(newlist))
	load(strcat(dirname,'matfiles1/',newlist(j).name));
	if(ctfparams~=-1) 
	  if(abs(ctfparams(1)-abs(dforig))<1e-6)
	    dfice = ctfparams(1); 
	    plot(dfcarbon*1e6,dfice*1e6,'r.');
        k = k+1;
	  end 
	end 
      end 
    end 
  else 
    l = l+1; 
  end 
end 

xlabel('Defocus estimated using carbon support film (\mum )'); 
