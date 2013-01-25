function [out D] = KSVDDenoiseMRC(mrcpath,mrcname,savepath,stackparams,ksvdparams)

savedictpath = [savepath '/dict/'];
savemrcpath = [savepath '/mrc/'];
savetiffpath = [savepath '/tiff/'];

if nargin < 6
    Df = [];
end

disp(' ')
disp(savedictpath)
if ~exist(savedictpath,'dir')
    reply = ...
        input(['Save Dictionary Path does not exist would you like to create it?'...
        ' Y/N [Y]:'],'s');
    if isempty(reply)
        reply = 'Y';
    end
    if strcmpi(reply,'y')
        mkdir(savedictpath)
    else
        disp('Exiting')
        return;
    end
end

disp(' ')
disp(savemrcpath)
if ~exist(savemrcpath,'dir')
    reply = input(['Save MRC Path does not exist would you like to create it?'...
        ' Y/N [Y]:'],'s');
    if isempty(reply)
        reply = 'Y';
    end
    if strcmpi(reply,'y')
        mkdir(savemrcpath)
    else
        disp('Exiting')
        return;
    end
    
end
%
% disp(' ')
% disp(savetiffpath)
% if ~exist(savetiffpath,'dir')
%     reply = input(['Save tiff does not exist would you like to create it?'...
%         ' Y/N [Y]:'],'s');
%     if isempty(reply)
%         reply = 'Y';
%     end
%     if strcmpi(reply,'y')
%         mkdir(savetiffpath)
%     else
%         disp('Exiting')
%         return;
%     end
%
% end


%%
disp(' ')
disp('Starting Sliding Window')
[stack rez] = readMRCandStack([mrcpath '/' mrcname],stackparams.na,...
    stackparams.start,stackparams.nslice,stackparams.roi);


%%
disp(' ')
disp('Finding Initial Dictionary')
[~, b] =  fileparts(mrcname);

ksvdparams.x = mean(stack,3);
[D] = makeKSVDdict(ksvdparams);

saveDictionary(D,inf,stackparams.roi,ksvdparams,[savedictpath '/' b '/']);
ksvdparams = rmfield(ksvdparams,'x');



for i = 1:size(stack,3)
    ksvdparams.initdict = D;
    ksvdparams.x = stack(:,:,i);
    [out(:,:,i),Dict(:,:,i)] = ksvddenoise(ksvdparams,5);
end

saveDictionary(Dict,stackparams.na,stackparams.roi,ksvdparams,[savedictpath '/' b '/']);

str = sprintf('%d_%d_%d_%d',stackparams.roi(1),stackparams.roi(2),stackparams.roi(3),stackparams.roi(4));
savemrcname = [b ...
    '_denoised_' 'KSVDSingleFrame' '_DictSize' num2str(ksvdparams.dictsize)...
    '_BlkSize' num2str(ksvdparams.blocksize) '_Sigma' num2str(ksvdparams.sigma)...
    '_AvgWinLen' num2str(stackparams.na) '_roi' str '.mrc'];

WriteMRC(out,rez,[ savemrcpath '/' savemrcname]);
