function [dictname] = saveDictionary(D,na,roi,params,dictdir)

roi
str = sprintf('%d_%d_%d_%d',roi(1),roi(2),roi(3),roi(4));


dictname = ['/dict_Dsize' num2str(params.dictsize)...
    '_blocksize' num2str(params.blocksize) '_sigma' num2str(params.sigma)...
    '_avg' num2str(na) '_roi' str];
disp([dictname '/' dictname '.mat'])

if ~exist([dictdir],'dir')
    mkdir([dictdir])
end

clear params.x
save([dictdir '/' dictname '.mat'],'D','roi','na','params')

end