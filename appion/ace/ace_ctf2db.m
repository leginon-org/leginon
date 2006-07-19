function varargout = ace_ctf2db(varargin)
%
% DESCRIPTION: 
%     Place the output of an ACE run into the database.
%
% USAGE: 
%     Use "doc ace_ctf2db" for details. 
%
% Copyright 2004 Satya P. Mallick
% Modified to insert to database by Gabe Lander 06/08/05 

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @acedemo_OpeningFcn, ...
                   'gui_OutputFcn',  @acedemo_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before acedemo is made visible.
function acedemo_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% varargin   command line arguments to acedemo (see VARARGIN)

% Choose default command line output for acedemo
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);
acecolor = [0.8 0.8 0.85]; 
set(handles.mainwindow,'Color',acecolor); 
set(handles.fileanddirpanel,'BackgroundColor',acecolor); 
set(handles.opimgpanel,'BackgroundColor',acecolor); 
set(handles.uipanel13,'BackgroundColor',acecolor); 
set(handles.title,'BackgroundColor',acecolor); 
set(handles.runnamepanel,'BackgroundColor',acecolor);
set(handles.text18,'BackgroundColor',acecolor);
set(handles.text19,'BackgroundColor',acecolor);

function expname_Callback(hObject, eventdata, handles)
update_expdir(handles);

% --- Executes during object creation, after setting all properties.
function expname_CreateFcn(hObject, eventdata, handles)

% --- Outputs from this function are returned to the command line.
function varargout = acedemo_OutputFcn(hObject, eventdata, handles) 
% Get default command line output from handles structure
varargout{1} = handles.output;

% --- Executes on button press in browse.
function browse_Callback(hObject, eventdata, handles)
  dirname = uigetdir(); 
  set(handles.dirname,'String',dirname,'Value',[]); 
  set(handles.expdir,'String',dirname);
  load_listbox(handles);

function display_Callback(hObject, eventdata, handles)

% --- Executes on button press in process.
function process_Callback(hObject, eventdata, handles)
  expname = get(handles.expname,'String'); % Experiment name
  runname = get(handles.runname,'String'); % Run name
  list_index = get(handles.filelist,'Value');
  list = get(handles.filelist,'String');
  dirname = get(handles.dirname,'String');
  opdirname = get(handles.opdirname,'String');
  if(dirname(end)~='/')
    dirname = strcat(dirname,'/'); 
  end 
  
  if(length(list_index)<1)
    fprintf('Please select (highlight) atleast one file\n'); 
    fprintf('Left Click : Selects one file\n'); 
    fprintf('Left Click + CTRL : Selects multiple files\n');     
    fprintf('Left Click + SHIFT : Selects multiple continuously listed files\n');         
  end 
  
  % make gui invisible
  set(handles.mainwindow,'Visible','off');
  pause(1);
  fprintf('Processing: Start\n'); 
  
  for i=1:length(list_index)
    filename = cell2mat(list(list_index(i)));
    fullname = strcat(dirname,filename);
    imgname = strrep(filename,'.mat','');
    load(fullname);
    opimg1name = strcat(opdirname,imgname,'1.png');
    opimg2name = strcat(opdirname,imgname,'2.png');
    % make sure that repsective opimages exist before
    % adding to the database
    if ~(exist(opimg1name))
        fprintf('Error:\n');
        fprintf('File ');
        fprintf(opimg1name);
        fprintf(' does not exist.\n');
        return
    end 
    if ~(exist(opimg1name))
        fprintf('Error:\n');
        fprintf('File ');
        fprintf(opimg1name);
        fprintf(' does not exist.\n');
        return
    end
    
    conn = connect_db('dbemdata');
    query = strcat('select Name as Experiment, `image path` as Path, DEF_id as experimentId from SessionData where name like "',expname,'"');
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','cellarray');
    result = fetch(curs);
    expdirname = cell2mat(result.Data(2));
    expid = cell2mat(result.Data(3));
    expdirname  = strcat(expdirname,'/');
    
    query = strcat('select a.`DEF_id` as legimgId, a.`REF|PresetData|preset` as legpresetId, `scope`.`defocus` from AcquisitionImageData a left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) where a.`MRC|image` = "',imgname,'"');
    curs = exec(conn, query);
    setdbprefs('DataReturnFormat','numeric');
    result = fetch(curs);

    legimgId = result.Data(1);
    legpresetId = result.Data(2);
    dforig = result.Data(3);
    dbctf(expid, runname, legimgId, legpresetId, imgname,abs(dforig),ctfparams,opimg1name,opimg2name,fullname)
    fprintf(filename);
    fprintf(' inserted\n');
  end
  fprintf('Processing: End\n');
  set(handles.mainwindow,'Visible','on');

function help_Callback(hObject, eventdata, handles)
  doc acedemo

% --- Executes on selection change in filelist.
function filelist_Callback(hObject, eventdata, handles)

% --- Executes during object creation, after setting all properties.
function filelist_CreateFcn(hObject, eventdata, handles)
  if ispc
    set(hObject,'BackgroundColor','white');
  else
    set(hObject,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
  end


function load_listbox(handles)
  list = '' ;
  dirname = get(handles.dirname,'String');
  if(dirname(end)~='/')
    dirname = strcat(dirname,'/');
  end 
  filefilter = get(handles.filefilter,'String'); 
  dir_struct = dir(strcat(dirname,filefilter));
  list = {dir_struct.name}'; 
  set(handles.filelist,'String',list);
  
function dirname_Callback(hObject, eventdata, handles)
  dirname = get(handles.dirname,'String');
  list_of_dirs = dir(dirname); 
  ind = find([list_of_dirs(:).isdir]==1); 
  if(dirname(end)~='/')
    dirname = strcat(dirname,'/');
    set(handles.dirname,'String',dirname);
  end
  load_listbox(handles);
  set(handles.expdir,'String',dirname);  
  
% --- Executes during object creation, after setting all properties.
function dirname_CreateFcn(hObject, eventdata, handles)
  if ispc
      set(hObject,'BackgroundColor','white');
  else
      set(hObject,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
  end

function opdirname_Callback(hObject, eventdata, handles)
  opdirname = get(handles.opdirname,'String');
  list_of_dirs = dir(opdirname); 
  ind = find([list_of_dirs(:).isdir]==1); 
  if(opdirname(end)~='/')
    opdirname = strcat(opdirname,'/');
    set(handles.opdirname,'String',opdirname);
  end
  set(handles.opexpdir,'String',opdirname);  


% --- Executes during object creation, after setting all properties.
function opdirname_CreateFcn(hObject, eventdata, handles)
if ispc
    set(hObject,'BackgroundColor','white');
else
    set(hObject,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
end

function filefilter_Callback(hObject, eventdata, handles)
  load_listbox(handles);

function filefilter_CreateFcn(hObject, eventdata, handles)
  if ispc
      set(hObject,'BackgroundColor','white');
  else
      set(hObject,'BackgroundColor',get(0,'defaultUicontrolBackgroundColor'));
  end

function runname_Callback(hObject, eventdata, handles)

function runname_CreateFcn(hObject, eventdata, handles)
    set(hObject,'BackgroundColor','white');

function update_expdir(handles) 
  conn = connect_db('dbemdata');
  expname = get(handles.expname,'String');
  query = strcat('select Name as Experiment, `image path` as Path from SessionData where name like "',expname,'"');
  
  curs = exec(conn, query);
  setdbprefs('DataReturnFormat','cellarray');
  result = fetch(curs);
  if(length(result.Data)>1)
      dirname = cell2mat(result.Data(2));
      dirname  = strcat(dirname,'/');
      dirname = strrep(dirname,'rawdata/','');
      matdirname = strcat(dirname,'ctf_ace/',expname,'/matfiles/');
      opdirname = strcat(dirname,'ctf_ace/',expname,'/opimages/');
      set(handles.expdir,'String',matdirname);
      set(handles.opexpdir,'String',opdirname);
      set(handles.dirname,'String',matdirname);
      set(handles.opdirname,'String',opdirname);
      load_listbox(handles)
  else 
     set(handles.expdir,'String','');  
  end 

% --- Executes on button press in opimgbrowse.
function opimgbrowse_Callback(hObject, eventdata, handles)
  opdirname = uigetdir(); 
  set(handles.opdirname,'String',opdirname,'Value',[]); 
  set(handles.opexpdir,'String',opdirname);
  load_listbox(handles);
