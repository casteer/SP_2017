
# For me (Ubuntu) I needed to install the wget module (details are here: https://ubuntuforums.org/showthread.php?t=2287729) 
import wget
import os
import numpy as np 
import time
import json
import sys


# Return a string with the path to the data on the web
def folder_path(sat_number,day,month,year):
	# Add check on whether the satellite number is sensible here.

	# The data web address 
	base = 'https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/gps/data/'
	return base + 'ns' + str(sat_number) + '/';

# To unit test this function 
# fpath = folder_path(41,07,01,01);
# print('Folder path is : ', fpath); 
	
	
# Return a string with the path to the filename on the web
def file_path(sat_number,day,month,year):
	# Add input checks here (e.g. is the day less than 30?)  

	# Get the folder path 
	folder = folder_path(sat_number,day,month,year);
	# Datafile version number 
	version_number = 'v1.03';# Check whether this varies between the satellite datasets?
	# Create the filename 
	return 'ns' + str(sat_number) + '_' + str(year).zfill(2) + str(month).zfill(2) + str(day).zfill(2) + '_' + version_number + '.ascii';
# To unit test this function 
# filepath = file_path(41,07,01,01);
# print('File path is : ', filepath); 


# Helper function to find the file size
def file_size(fname):  
        statinfo = os.stat(fname)  
        return statinfo.st_size  


# Function to download the selected data
def download_data(sat_number,day,month,year):

	# Get the filename 
	filename = file_path(sat_number,day,month,year);

	# Get the folder 
	folder = folder_path(sat_number,day,month,year);

	# Download file
	wget_file = wget.download(folder+filename);

	# Check if we've downloaded the 404 notice or actual data
	fs = file_size(filename);#This throws an error when wget hasn't finished 
	if(fs<10000):
		print('Check the filename as the returned file appears too small');
		print('... deleting file');
		os.remove(filename);
		return 1;
	else:
		return 0;
# Unit test : This should download a 404 (not found) file and then delete it (done = 1)
#done = download_data(41,01,01,01);
#print(done);
# Unit test : This should download an actual data file (done = 0)
#done = download_data(41,07,01,01);
#print(done);

# Downloads the data in a given time range 
def get_data_range(sat_numbers,days,months,years):

	for this_sat in sat_numbers:
		for this_year in years:
			for this_month in months:
				for this_day in days:
					done = download_data(this_sat,this_day,this_month,this_year);
			
	return 0;
# Unit test : Gets all data in January 2001
# get_data_range([41],np.arange(31),[01],[01]);



# Creates a JSON header from the datafile
def create_json_header(filename):

	# Opens up the datafile
	log = open(filename, 'r');
      	reading = log.readlines()[5:];

	# Creates a file header to store info about columns for one iteration
	json_filename = filename[:-6] + '.json';
      	header = open(json_filename, "w+")
      	for line in reading:
        	if line.startswith('#'):
            		li = line.strip('#')
            		header.write(li)
      	header.close()
	return json_filename;
# Unit test : Creates a JSON file corresponding to the .ascii file
# filename = file_path(41,07,01,01);
# create_json_header(filename);# Should see a JSON file in the directory now


# Loads a data file using information from the JSON header file 
def load_data(json_filename,data_filename):

	# Open up the json file	
	head = json.load(open(json_filename)); #load header file
      	f = np.loadtxt(data_filename); #use numpy library to create arrays

	variables = {}
      	for x, value in head.items():
        	i = value['START_COLUMN']
        	j = i + value['DIMENSION'][0]
        	variables.update({x: f[ : , i : j] for column in head});

	return variables;
# Unit test : Loads the data and prints it
# data_filename = file_path(41,07,01,01);
# data = load_data(create_json_header(data_filename),data_filename)
# print(data);

# Does the data contain the chosen day? Note the day is decimal 
def check_day(data,chosen_day):
	min_day_test = ( chosen_day>=np.min(data["decimal_day"]) );
	max_day_test = ( chosen_day<=np.max(data["decimal_day"]) );
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

# Is the satellite ever inside a given altitude range (in Earth radii)? 
def check_altitude(data,max_alt):
	max_alt_test = ( np.max(data["Rad_Re"]) < max_alt);
	if(max_alt_test):
		return True;
	else:
		return False;
# Unit test : Does the data contain the chosen day
#data_filename = file_path(41,07,01,01);
#data = load_data(create_json_header(data_filename),data_filename);
#flag = check_altitude(data,30);# Should give true
#print(flag);
#flag = check_altitude(data,1);# Should give false
#print(flag);





