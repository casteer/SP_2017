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
        self.fail_load=False;
        
        # Check if the file is available locally in this folder?
        exist_test = os.path.isfile(self.data_filename);
        if(not exist_test):
            # No it's been downloaded so download it
            print 'Downloading ' + self.data_filename;
            if(self.download()):
                self.fail_load=True;
                return;
        else:
            print 'File ' + self.data_filename + ' already exists ';
            
        if(not self.fail_load):
    
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

        print;
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
            
        # For the 2004-2005 new year, the decimal day goes negative 
        # across the end of year boundary ... need to investigate why this is? 
        if(last_day<0):
            last_day = 1+int(math.ceil(np.max(self.dataset[-1].data["decimal_day"])));

        # print first_day;
        # print last_day;

        # Convert the decimal day to month and the day
        epoch = datetime(2000+self.current_year - 1, 12, 31);
        result = epoch + timedelta(days=last_day);

        # print result; 
        self.dataset[-1].summary.print_summary();
            
        # Find the new month and day
        self.current_day = result.day;
        self.current_month = result.month;
        if(first_day>last_day):
            self.current_year = self.current_year + 1;
        else:
            self.current_year = result.year-2000;
            
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
    def __init__(self,name):
        
        self.name = name;
        
        # Geographic latitude and longitude
        self.data = dict();
        
        self.first_set=True;

    def add_data(self,name,value):
        self.data[name] = value;
        
    def add_date(self,mins,hh,dd,mm,yy):
        # Save in a date structure 
        self.date = datetime(day=dd,month=mm,year=2000+yy,hour=hh,minute=mins);
        # print self.date;
        year = self.date.year
        startOfThisYear = datetime(year=yy+2000, month=1, day=1);
        startOfNextYear = datetime(year=yy+2000+1, month=1, day=1);

        # secs_so_far = float((self.date - startOfThisYear).seconds);
        # secs_in_year = float((startOfNextYear-startOfThisYear).seconds);
        # print secs_so_far;
        
        decimal_day = float((self.date - startOfThisYear).days) + (float(hh)/24.0) + (float(mins)/(24.0*60.0));
      
        # print decimal_day;
        self.add_data("decimal_day",decimal_day+1.0);
        
        # Save decimal year too 
        # days_in_year = float((startOfNextYear-startOfThisYear).days);       
        # print days_in_year;
        # year_fraction = decimal_day/days_in_year;
        # self.add_data("decimal_year",2000+yy+year_fraction);
        self.add_data("year",2000+yy);


        
        
  #      self.add_data("decimal_year",fraction+yy+2000);

        # ayear = (datetime(year=2000+yy+1,month=1,day=1)-datetime(year=2000+yy,month=1,day=1)).total_seconds();
        # td = (datetime(day=dd,month=mm,year=2000+yy,hour=hh,minute=mins) - datetime(year=2000+yy,month=1,day=1)).total_seconds();
        
        # self.add_data("Decimal_",yy);
        # print td/ayear
        # print year_elapsed.year
        







        
        
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
        self.key_varnames = set();
        self.key_filenames = set();
        
        # Initialise indices array
        for sat_data in satellite_data.dataset[:]:
            # Create new set in the indices dictionary
            key_filename = sat_data.data_filename[:-12];
            self.key_filenames.add(key_filename);
            self.indices[key_filename] = dict();

        self.compare_with_zerocrossing(["decimal_day"]);

    def remove_empty_sets(self):
        # Print indices         
        for key_filename in self.key_filenames:
            for key_varname in self.key_varnames:
                if(self.indices[key_filename][key_varname]==set()):
                    print "Deleting " + key_filename + " " + key_varname;
                    del self.indices[key_filename][key_varname];
                    
            
        
        
    def get_indices_in_time_window(self, time_window_in_days):
        
        # For each search variable 
        for sat_data in self.satellite_data.dataset[:]:
 
            # Create new set in the indices dictionary
            key_filename = sat_data.data_filename[:-12];
            
            new_indices = set();
            for index in self.indices[key_filename]["decimal_day"]:

                decimal_day_event = self.event.data["decimal_day"];
                decimal_day_data = sat_data.data["decimal_day"][index];
                    
                upper_index=0;
                while(((upper_index+index)>0) and (math.fabs(decimal_day_data - decimal_day_event)<time_window_in_days)):
                    # print index, upper_index, decimal_day_data, decimal_day_event;
                    if(not ((index+upper_index) in self.indices[key_filename]["decimal_day"])):
                        new_indices.add(index+upper_index);                    
                    
                    upper_index-=1;
                    decimal_day_data = sat_data.data["decimal_day"][index+upper_index];


                upper_index=0;
                decimal_day_data = sat_data.data["decimal_day"][index];
                while (math.fabs(decimal_day_data - decimal_day_event)<time_window_in_days):
                    # print index,index+upper_index, decimal_day_data, decimal_day_event;
                    
                    if(not ((index+upper_index) in self.indices[key_filename]["decimal_day"])):
                        new_indices.add(index+upper_index);                    
                    
                    upper_index+=1;                    
                    decimal_day_data = sat_data.data["decimal_day"][index+upper_index];
                    
                    
            for ind in new_indices:
                self.indices[key_filename]["decimal_day"].add(ind);

            print;                
            print key_filename;
            print self.indices[key_filename];
            
            if (self.indices[key_filename]["decimal_day"]!=set()):            
                print min(sat_data.data["decimal_day"][ list(self.indices[key_filename]["decimal_day"])])
                print max(sat_data.data["decimal_day"][ list(self.indices[key_filename]["decimal_day"])])

    # This find the closest value to the event's value for the same keyname        
    def compare_with_zerocrossing(self,key_varnames):
        
        for sat_data in self.satellite_data.dataset[:]:
 
            # Create new set in the indices dictionary
            key_filename = sat_data.data_filename[:-12];

            for key_varname in key_varnames:
                
                self.key_varnames.add(key_varname);
                self.indices[key_filename][key_varname] = set();
               
                # Get the satellite's data
                sat_data_array = sat_data.data[key_varname];
                retain=False;

                # Get the sign of the first datapoint 
                del_data = (sat_data_array[0]-self.event.data[key_varname])  ;
                new_sign1 = np.sign(del_data);
                
                # Search for sign change in the difference
                for index,sat_data_element in enumerate(sat_data_array):

                    old_sign = new_sign1;
                    
                    del_data = (sat_data_element-self.event.data[key_varname])  ;
                    new_sign1 = np.sign(del_data);

                    # Check for crossing new year boundary in "decimal_day" data
                    if(key_varname=="decimal_day"):

                        startOfThisYear = datetime(year=self.event.date.year, month=1, day=1);
                        startOfNextYear = datetime(year=self.event.date.year+1, month=1, day=1);
                        days_in_year = float((startOfNextYear-startOfThisYear).days);       

                        del_data = (sat_data_element+days_in_year-self.event.data[key_varname]);
                        new_sign2 = np.sign(del_data);

                    else:
                        new_sign2 = new_sign1;
                        
                    if((new_sign1!=old_sign) and (new_sign2==new_sign1)):
                        retain=True;
                        
                    # Check for change of sign, ignore sign change at start of datafile
                    if(retain):
                        self.indices[key_filename][key_varname].add(index);
                        # var_sets[count].add(index);
                        retain=False;
               
                
                    
            # print sat_lat[indices];
# print long_zero_crossings;
                    
        self.print_indices();
        return 0;
    
    def print_indices(self):
        # Print indices         
        for key_filename in self.key_filenames:
            print;
            print key_filename;
            print self.indices[key_filename];
        
    def intersect_indices_set(self):
        # Save the set of indices of datapoints that are common to all search terms
        for key_filename in self.key_filenames:
            self.indices[key_filename]["intersection"] = self.indices[key_filename]["decimal_day"];
            for key_varname in self.key_varnames:
                self.indices[key_filename]["intersection"].intersection_update(self.indices[key_filename][key_varname]);
                print key_filename,key_varname, len(self.indices[key_filename]["intersection"])
        self.key_varnames.add("intersection");
    
    def compare_with_tolerance(self,key_varnames,tol=1e-4):
        
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
                retain=False;
                
                # Search for sign change in the difference
                for index,sat_data_element in enumerate(sat_data_array):

                    del_data = math.fabs(sat_data_element-self.event.data[key_varname])/math.fabs(sat_data_element);
                    
                    if(del_data<tol):
                        retain=True;
                        
                    # Check for change of sign, ignore sign change at start of datafile
                    if(retain):
                        var_sets[count].add(index);
                        retain=False;
                count+=1;
               
                
            # Save the set of indices of datapoints that are common to all search terms
            self.indices[key_filename] = var_sets[0];
            for iset in np.arange(1,count):
                self.indices[key_filename].intersection_update(var_sets[iset]);

            # Print indices
            self.print_indices();
                    
            # print sat_lat[indices];
# print long_zero_crossings;
                    
        return 0;

# This holds all of the data that searches over all satellites
class meta_search:
    def __init__(self,satellites_list):
        
        self.satellites = satellites_list;
        self.satellites_data = list();
        self.searches = list();

    # Searches for a single event over all satellites between the dates
    def apply_search(self,this_event):

        for sats_data in self.satellites_data:
            searches.append(search(this_event,sats_data));
        
        
    def load_data(self,start_date,end_date):
        
        for this_sat in self.satellites:
            # Extract the day,month,year from the start and end dates
            self.satellites_data.append(gps_satellite_data(this_sat,start_date.day,start_date.month,start_date.year));
        
            # Keeping downloading/reading data until beyond the desired end date            
            current_date = datetime(self.satellites_data[-1].current_year,self.satellites_data[-1].current_month,self.satellites_data[-1].current_day);
            finished = current_date>end_date;

            while ((not finished) and (not self.satellites_data[-1].dataset[-1].fail_load)):
                self.satellites_data[-1].get_next_datafile();
                
                # Update end condition 
                current_date = datetime(self.satellites_data[-1].current_year,self.satellites_data[-1].current_month,self.satellites_data[-1].current_day);
                finished = current_date>end_date;
                print (not finished)
            
            

d = datetime(4,12,26);
print d.date

                
sats = list();
sats.append(41);
for i in np.arange(54,61): 
    sats.append(i);
    
ms = meta_search(sats);

e = event("Boxing Day Earthquake");
e.add_date(mins=59,hh=00,dd=26,mm=12,yy=04);
e.add_data("Geographic_Latitude",3.24);
e.add_data("Geographic_Longitude",95.8);

start_date = datetime(04,12,19);
end_date = datetime(05,1,1);
start_date.day

ms.load_data(start_date,end_date);
#ms.apply_search(e);


#==============================================================================
# satellites_data = list();
# 
# searches = list();
# for this_sat in sats:
#     
# 
#     # satellite_data.save_disk_space=True;
#     for i in np.arange(0,5):
#         satellites_data[-1].get_next_datafile();
# 
#     # e.add_data("Rad_Re",130);
# 
# 
#     searches.append(search(e,satellites_data[-1]));
#     print "==================================================================="
#     searches[-1].compare_with_zerocrossing(["Geographic_Latitude"]);
#     print "==================================================================="
#     searches[-1].get_indices_in_time_window(0.5);
#     searches[-1].intersect_indices_set();
#     print "==================================================================="
#     searches[-1].print_indices();
#     searches[-1].remove_empty_sets();
#     searches[-1].print_indices();
#     
#==============================================================================


