%dirname = '/ami/data05/leginon/04jul20a/extract/ctf/04jul20a/';
dirname = '/ctf/04apr14b/'; % directory
list = dir(strcat(dirname,'matfiles_astig1/*.mat')); 
k=0; 
l=0; 
%figure;
hold on; 
for i=1:length(list) 
  
  load(strcat(dirname,'matfiles_astig1/',list(i).name));
  if(ctfparams~=-1) 
    if(abs(ctfparams(1)-abs(dforig))<1e-6)
      if(abs(ctfparams(2)-abs(dforig))<1e-6)
	if(abs(ctfparams(1) - ctfparams(2))<2e-6)
	      if(abs(ctfparams(1))>1e-6)
	
		k=k+1;
		plot(abs(dforig)*1e6,ctfparams(1)*0.7e6,'*');
	      end 
       end
      end
    end 
  else 
    l = l+1; 
    fprintf('%s \n',list(i).name); 
  end 
 
end 

fprintf('%d %d %d %f\n',l,k,length(list),k*100/(length(list))); 
