dirname = '/ctf/04apr14b/'; % directory

list = dir(strcat(dirname,'matfiles_astig1/*.mat')); 

k=1;
s=[]; 
err=[];
offset=1; 
th1=0.9*(offset+1)*20e-8; 
th2=0.3*(offset)*20e-8; 
count = 0; 
for i=1:length(list)-offset
  load(strcat(dirname,'matfiles_astig1/',list(i).name));
  df1 = ctfparams(1); 
  load(strcat(dirname,'matfiles_astig1/',list(i+offset).name));
  df2 = ctfparams(1);
  
  if(ctfparams~=-1)
    val = abs(df1-df2); 
    if(val<th1 && val>th2 )
      s(k) = val;
      err(k) = abs(20*offset*1e-8 - val);  
      k=k+1; 
    end
  
    count=count+1; 
  end
end 
fprintf('%f %f %f %f %f %d/%d\n',mean(s)*1e6,std(s)*1e6,mean(err)*1e6,th1*1e6,th2*1e6,length(s),count); 
