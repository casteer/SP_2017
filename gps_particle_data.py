# For me (Ubuntu) I needed to install the wget module (details are here: https://ubuntuforums.org/showthread.php?t=2287729) 
import wget
import os
import numpy as np 
import time
import json
import sys
import math
from datetime import datetime, timedelta
from itertools import compress


# This class holds all of the data and functions associated with a single data file
class gps_particle_datafile():
    # Variables in the data class 

    def __init__(self,sat_number,day,month,year):
        
        self.satellite_number = sat_number;
        self.day = day;
        self.month = month;
        self.year = year;
    
        # Generate the basepath and filename 
        self.basepath = self.folder_path();
        self.data_filename = self.file_path();
        
        # Check if the file is available locally in this folder?
        exist_test = os.path.isfile(self.data_filename);
        if(not exist_test):
            # No it's been downloaded so download it
            print 'Downloading ' + self.data_filename;
            self.download();
        else:
            print 'File ' + self.data_filename + ' already exists ';

        # Create the JSON header file
        self.json_filename = self.create_json();

        # Read the data from the file 
        self.data = self.read();

        # Create the summary of the data for searching
        self.summary = self.gps_particle_datafile_summary(self.data);
        # self.summary.print_summary();


    # Return a string with the path to the data on the web
    def folder_path(self):
        # Add check on whether the satellite number is sensible here.
        # The data web address 
        base = 'https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/gps/data/'
        return base + 'ns' + str(self.satellite_number) + '/';

    # To unit test this function 
    # fpath = folder_path(41,07,01,01);
    # print('Folder path is : ', fpath); 
    
    # Return a string with the path to the filename on the web
    def file_path(self):
        # Add input checks here (e.g. is the day less than 31?)  
        # Datafile version number 
        version_number = 'v1.03';# Check whether this varies between the satellite datasets?
        # Create the filename 
        return 'ns' + str(self.satellite_number) + '_' + str(self.year).zfill(2) + str(self.month).zfill(2) + str(self.day).zfill(2) + '_' + version_number + '.ascii';
    # To unit test this function 
    # filepath = file_path(41,07,01,01);
    # print('File path is : ', filepath); 


    # Helper function to find the file size
    def file_size(self,fname):  
            statinfo = os.stat(fname)  
            return statinfo.st_size  


    # Function to download the selected data
    def download(self):

        # Download file
        wget_file = wget.download(self.basepath+self.data_filename);

        # Check if we've downloaded the 404 notice or actual data
        fs = self.file_size(self.data_filename);#This throws an error when wget hasn't finished 
        if(fs<10000):
            print('Check the filename as the returned file appears too small');
            print('... deleting file');
            os.remove(self.data_filename);
            return 1;
        else:
            return 0;
    # Unit test : This should download a 404 (not found) file and then delete it (done = 1)
    #done = download_data(41,01,01,01);
    #print(done);
    # Unit test : This should download an actual data file (done = 0)
    #done = download_data(41,07,01,01);
    #print(done);

    # Loads a data file using information from the JSON header file 
    def read(self):

        # Open up the json file    
        head = json.load(open(self.json_filename)); #load header file
        f = np.loadtxt(self.data_filename); #use numpy library to create arrays

        print 'Reading file ' + self.data_filename;

        variables = {};
        for x, value in head.items():
            i = value['START_COLUMN']
            j = i + value['DIMENSION'][0]
            variables.update({x: f[ : , i : j] for column in head});
            # print variables;
        return variables;
    # Unit test : Loads the data and prints it
    # data_filename = file_path(41,07,01,01);
    # data = load_data(create_json_header(data_filename),data_filename)
    # print(data);


    # Creates a JSON header from the datafile
    def create_json(self):

        # Opens up the datafile
        log = open(self.data_filename, 'r');
        reading = log.readlines()[5:];
    
        # Creates a file header to store info about columns for one iteration
        self.json_filename = self.data_filename[:-6] + '.json';
        header = open(self.json_filename, "w+")
        for line in reading:
            if line.startswith('#'):
                li = line.strip('#')
                header.write(li)
        header.close()
        return self.json_filename;
    # Unit test : Creates a JSON file corresponding to the .ascii file
    # filename = file_path(41,07,01,01);
    # create_json_header(filename);# Should see a JSON file in the directory now


    # Helper class to handle the summary data 
    class gps_particle_datafile_summary():
        def __init__(self,data):
            self.min_latitude=np.min(data["Geographic_Latitude"]);
            self.max_latitude=np.max(data["Geographic_Latitude"]);
            self.min_longitude=np.min(data["Geographic_Longitude"]);
            self.max_longitude=np.max(data["Geographic_Longitude"]);
            self.min_radius_RE=np.min(data["Rad_Re"]);
            self.max_radius_RE=np.max(data["Rad_Re"]);
            self.min_decimal_day = float(data["decimal_day"][0]);
            self.max_decimal_day = float(data["decimal_day"][-1]);
            self.year = np.min(data["year"]);
            self.min_L_shell = np.min(data["L_shell"]);
            self.max_L_shell = np.max(data["L_shell"]);

        def print_summary(self):
            print;
            print 'Min Latitude         : ', self.min_latitude;
            print 'Max Latitude         : ', self.max_latitude;

            print 'Min Longitude         : ', self.min_longitude;
            print 'Max Longitude         : ', self.max_longitude;

            print 'Min Radius         : ', self.min_radius_RE;
            print 'Max Radius         : ', self.max_radius_RE;

            print 'Min L Shell         : ', self.min_L_shell;
            print 'Max L Shell        : ', self.max_L_shell;

            print 'Min Day            : ', self.min_decimal_day;
            print 'Max Day            : ', self.max_decimal_day;

            print 'Year             : ', self.year;
            print;

        # Is the chosen day in this dataset?
        def check_decimal_day(self,chosen_day):
            min_day_test = ( chosen_day>=self.min_decimal_day );
            max_day_test = ( chosen_day<=self.max_decimal_day );
            if(min_day_test and max_day_test):
                return True;
            else:
                return False;
        # Unit test : Does the data contain the chosen day
        #data_filename = file_path(41,07,01,01);
        #data = load_data(create_json_header(data_filename),data_filename);
        #flag = check_day(data,8);# Should give true
        #print(flag);
        #flag = check_day(data,2);# Should give false
        #print(flag);
    
        # Is the chosen L shell  in this dataset?
        def check_L_shell(self,chosen_L):
            min_test = ( chosen_L>=self.min_L_shell );
            max_test = ( chosen_L<=self.max_L_shell );
            if(min_test and max_test):
                return True;
            else:
                return False;
    
        # Is the satellite below a given Re?
        def check_L_shell(self,chosen_Re):
            min_test = ( chosen_Re>=self.min_radius_RE );
            max_test = ( chosen_Re<=self.max_radius_RE );
            if(min_test and max_test):
                return True;
            else:
                return False;    
        
# This class is holds all of the data and functions associated with a single satellite
class gps_satellite_data():

    
    def __init__ (self,satellite_number,day,month,year):

        self.save_disk_space = False;# Deletes the downloaded file once the data has been loaded into this data structure

        # Create a list of datasets     
        self.dataset = [];    
        # Append the first datafile into the list 
        self.dataset.append(gps_particle_datafile(satellite_number,day,month,year));

        self.satellite_number=satellite_number;
        self.current_day=day;
        self.current_month=month;
        self.current_year=year;

        # Delete the file if this flag is set                
        if(self.save_disk_space):
            print 'Saving disk space, deleting file : ', self.dataset[0].data_filename;
            os.remove(self.dataset[0].data_filename);


    def get_next_datafile(self):
        
        # Get the current size of the dataset list 
        curr_len = len(self.dataset);

        # Get the first and last day of the current datafile
        first_day = int(math.ceil(self.dataset[-1].summary.min_decimal_day));
        last_day = int(math.ceil(self.dataset[-1].summary.max_decimal_day));

        # Convert the decimal day to month and the day
        epoch = datetime(2000+self.current_year - 1, 12, 31);
        result = epoch + timedelta(days=last_day);

        # Find the new month and day
        self.current_day = result.day;
        self.current_month = result.month;
        if(first_day>last_day):
            self.current_year = self.current_year + 1;

        # Load the new data 
        self.dataset.append(gps_particle_datafile(self.satellite_number,self.current_day,self.current_month,self.current_year));

        # Delete the file if this flag is set                
        if(self.save_disk_space):
            print 'Saving disk space, deleting file : ', self.dataset[-1].data_filename;
            os.remove(self.dataset[-1].data_filename);

        if(curr_len==len(self.dataset)):
            return 1;
        else:
            return 0;

# UNIT TEST: 
# This loads the first datafile
# satellite_data = gps_satellite_data(41,16,12,01);
# This loads all of the data for the single satellite
# while(satellite_data.get_next_datafile()==0):
#    print;

# This holds the data associated with an event (e.g. earthquake)
class event():
    def __init__(self, name, year,month,day,hour):
        
        self.date = datetime(year,month,day,hour);
        self.name = name;
        
        # Geographic latitude and longitude
        self.data = dict();
        
        self.first_set=True;

    def add_data(self,name,value):
        self.data[name] = value;
        
# Defines a data search 
class search():
    def __init__(self, event, satellite_data):
        
        # Create the indices of the satellites
        # self.satellites = np.arange(53,74);
        # self.satellites = np.insert(satellites,0,41);
        # self.satellites = np.insert(satellites,1,48);
        self.satellite_data = satellite_data;
        self.event = event;
        self.indices = dict();# dictionary of sets of indices of the dataset, keyed by filename

    def find_zero_crossing(self,data):
        signed_data = np.sign(data);
        pos = signed_data>0;
        npos = ~pos;        
        pos2neg_cross = np.bitwise_and(npos[:-1],pos[1:]);
        neg2pos_cross= np.bitwise_and(pos[:-1], npos[1:]);
        crossings = np.bitwise_or(pos2neg_cross, neg2pos_cross);

        return crossings;
        
    
        
    def compare(self,key_varnames):
            
        for sat_data in satellite_data.dataset[:]:

            # Create new set in the indices dictionary
            key_filename = sat_data.data_filename[:-12];
                
            self.indices[key_filename] = set();
                
            count=0;
            var_sets={};
            for key_varname in key_varnames:
                var_sets[count] = set();

                # Get the satellite's data
                sat_data_array = sat_data.data[key_varname];
        
                # Search for sign change in the difference
                cand_indices = self.find_zero_crossing(sat_data_array - self.event.data[key_varname]*np.ones(sat_data_array.shape));

                for i in np.where(cand_indices)[0][0:-1]:
                    var_sets[count].add(i);                
                count+=1;
                    
            self.indices[key_filename] = var_sets[0];
            for iset in np.arange(1,count):
                self.indices[key_filename].intersection_update(var_sets[iset]);
                

            # Print indices
            print key_filename
            print self.indices[key_filename];
                    
                    
                    # print sat_lat[indices];
                    # print long_zero_crossings;
                    
        return 0;
                


satellite_data = gps_satellite_data(41,16,12,01);
for i in np.arange(0,10):
    satellite_data.get_next_datafile();

e = event("An earthquake", 12,12,12,01);
e.add_data("Geographic_Latitude",53);
e.add_data("Geographic_Longitude",80);
# e.add_data("Rad_Re",130);

s = search(e,satellite_data);
s.compare(["Geographic_Latitude","Geographic_Longitude"]);

# print satellite_data.dataset[-1].data.get("Geographic_Latitude");




