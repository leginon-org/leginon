function dbctf(expid, runname, legimgId, legpresetId, imagename,defocus_nom,ctfparams,graph1,graph2,mat_file)
% 
% Writes to Leginon database. 
%
% Usage : 
%        dbctf(expid, runname, legimgId, legpresetId, imagename,defocus_nom,ctfparams,graph1,graph2,mat_file)
%
% Copyright 2004 Denis Fellman and Satya P. Mallick

defocus1 = ctfparams(1); 
defocus2 = ctfparams(2);
defocusinit = ctfparams(3); 
amplitude_constrast = ctfparams(4);
angle_astigmatism = ctfparams(5)*180/pi; 
noise1 = ctfparams(6);
noise2 = ctfparams(7); 
noise3 = ctfparams(8);
noise4 = ctfparams(9); 
envelope1 = ctfparams(10); 
envelope2 = ctfparams(11); 
envelope3 = ctfparams(12);
envelope4 = ctfparams(13);  
lowercutoff = ctfparams(14);
uppercutoff = ctfparams(15);
snr = ctfparams(16); 
confidence = ctfparams(17); 
confidence_d = ctfparams(18);
blobgraph1 = file2hexstr(graph1); 
blobgraph2 = file2hexstr(graph2); 

conn = connect_db('processing');


%get default leginon image Id

%check if image exists in 
query = ['select imageId from `image` where imagename like "'  imagename '" order by imageId desc limit 1'];
curs = exec(conn, query);
setdbprefs('DataReturnFormat','numeric');
result = fetch(curs);
imageId = result.Data; 

if iscell(imageId)
	imageId = cell2mat(imageId);
end

if imageId == 'No Data'
	% insert image and get a imageId
	fields = { '`defocus_nominal`' , '`imagename`', '`sessionId`' , '`DEF_id`', '`REF|PresetData|preset`'};
	values = { defocus_nom, imagename,expid , legimgId, legpresetId};
	insert(conn, 'image', fields, values); 
	
	% get last inserted imageId
	query = 'SELECT imageId FROM image WHERE imageId IS NULL;';
	curs = exec(conn, query);
	result = fetch(curs);
	imageId = result.Data;
end

if iscell(imageId)
	imageId = cell2mat(imageId);
end


%check if run name exists in 
query = ['select runId from `run` where name like "'  runname '" and sessionId="' num2str(expid) '" order by runId desc limit 1'];
curs = exec(conn, query);
setdbprefs('DataReturnFormat','numeric');
result = fetch(curs);
runId = result.Data; 

if iscell(runId)
	runId = cell2mat(runId);
end

if runId == 'No Data'
	% insert run name and get a runId
	fields = { 'name', 'sessionId' };
	values = { runname, expid };
	insert(conn, 'run', fields, values); 
	
	% get last inserted runId
	query = 'SELECT runId FROM run WHERE runId IS NULL;';
	curs = exec(conn, query);
	result = fetch(curs);
	runId = result.Data;
end
if iscell(runId)
	runId = cell2mat(runId);
end


%check for failed CTF estimation and insert ctf data
if defocus1==-1,
	ctf_fields = { 'runId', 'imageId'};
	ctf_values = { runId, imageId };
else,
	ctf_fields = { 'runId', 'imageId', 'defocus1', 'defocus2', 'defocusinit','amplitude_constrast', 'angle_astigmatism', 'noise1', 'noise2', 'noise3', 'noise4', 'envelope1', 'envelope2', 'envelope3', 'envelope4', 'lowercutoff', 'uppercutoff', 'graph1', 'graph2', 'mat_file', 'snr', 'confidence','confidence_d'};
	ctf_values = { runId, imageId, defocus1, defocus2, defocusinit, amplitude_constrast, angle_astigmatism, noise1, noise2, noise3, noise4, envelope1, envelope2, envelope3, envelope4, lowercutoff, uppercutoff, graph1, graph2, mat_file, snr, confidence, confidence_d };
end

insert(conn, 'ctf', ctf_fields, ctf_values) 

% get last inserted  ctfId to insert blobs
query = 'SELECT ctfId FROM ctf WHERE ctfId IS NULL;';
curs = exec(conn, query);
result = fetch(curs);
ctfId = result.Data;

if iscell(ctfId)
	ctfId = cell2mat(ctfId);
end

%insert ctf blobs
ctfblob_fields = { 'imageId', 'ctfId', 'blobgraph1', 'blobgraph2' };
ctfblob_values = { imageId, ctfId, blobgraph1, blobgraph2 };

insert_blob(conn, 'ctfblob', ctfblob_fields, ctfblob_values) 

%close database cursor and connection
close(curs);

