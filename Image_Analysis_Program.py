#' % Image_Analysing_Program Sample
#' ECO, Thermodrone1.0


#' This is an example HTML publish script for EME185_Project.py.
#' To run the actual program with thermal images taken, run pypublish Image_Analysing_Program on command prompt.

#+ term=False
#+ echo=False
import pandas as pd
import numpy as np
from skimage import data, filters
import subprocess
import sys
import os
import math
from PIL import Image
from matplotlib import cm
import subprocess
import io
import json
from math import sqrt, exp, log
from os import listdir
from os.path import isfile, join
import cv2
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
import skimage
from skimage import feature, data, filters
from skimage.filters import threshold_adaptive
from skimage.feature import peak_local_max, canny
from skimage.measure import regionprops
import matplotlib.patches as mpatches
from skimage.morphology import label
import datetime
import requests

def raw2temp(raw, E=.95, OD=1, RTemp=20, ATemp=20, IRWTemp=20, IRT=1, RH=50, PR1=21106.77, PB=1501, PF=1, PO=-7340,
             PR2=0.012545258):
    """ convert raw values from the flir sensor to temperatures in C """
    # this calculation has been ported to python from https://github.com/gtatters/Thermimage/blob/master/R/raw2temp.R
    # a detailed explanation of what is going on here can be found there

    # constants
    ATA1 = 0.006569
    ATA2 = 0.01262
    ATB1 = -0.002276
    ATB2 = -0.00667
    ATX = 1.9

    # transmission through window (calibrated)
    emiss_wind = 1 - IRT
    refl_wind = 0

    # transmission through the air
    h2o = (RH / 100) * exp(1.5587 + 0.06939 * (ATemp) - 0.00027816 * (ATemp) ** 2 + 0.00000068455 * (ATemp) ** 3)
    tau1 = ATX * exp(-sqrt(OD / 2) * (ATA1 + ATB1 * sqrt(h2o))) + (1 - ATX) * exp(
        -sqrt(OD / 2) * (ATA2 + ATB2 * sqrt(h2o)))
    tau2 = ATX * exp(-sqrt(OD / 2) * (ATA1 + ATB1 * sqrt(h2o))) + (1 - ATX) * exp(
        -sqrt(OD / 2) * (ATA2 + ATB2 * sqrt(h2o)))

    # radiance from the environment
    raw_refl1 = PR1 / (PR2 * (exp(PB / (RTemp + 273.15)) - PF)) - PO
    raw_refl1_attn = (1 - E) / E * raw_refl1
    raw_atm1 = PR1 / (PR2 * (exp(PB / (ATemp + 273.15)) - PF)) - PO
    raw_atm1_attn = (1 - tau1) / E / tau1 * raw_atm1
    raw_wind = PR1 / (PR2 * (exp(PB / (IRWTemp + 273.15)) - PF)) - PO
    raw_wind_attn = emiss_wind / E / tau1 / IRT * raw_wind
    raw_refl2 = PR1 / (PR2 * (exp(PB / (RTemp + 273.15)) - PF)) - PO
    raw_refl2_attn = refl_wind / E / tau1 / IRT * raw_refl2
    raw_atm2 = PR1 / (PR2 * (exp(PB / (ATemp + 273.15)) - PF)) - PO
    raw_atm2_attn = (1 - tau2) / E / tau1 / IRT / tau2 * raw_atm2
    raw_obj = (
                raw / E / tau1 / IRT / tau2 - raw_atm1_attn - raw_atm2_attn - raw_wind_attn - raw_refl1_attn - raw_refl2_attn)

    # temperature from radiance
    temp_C = PB / log(PR1 / (PR2 * (raw_obj + PO)) + PF) - 273.15

    return temp_C


def _parse_temp(temp_str):
    # TODO: do this right
    # we assume degrees celsius
    return (float(temp_str.split()[0]))


def _parse_length(length_str):
    # TODO: do this right
    # we assume meters
    return (float(length_str.split()[0]))


def _parse_percent(percentage_str):
    return (float(percentage_str.split()[0]))


def extract_thermal(flir_image_path):
    """ extracts the thermal image as 2D numpy array with temperatures in C """

    # read image metadata needed for conversion of the raw sensor values
    # E=1,SD=1,RTemp=20,ATemp=RTemp,IRWTemp=RTemp,IRT=1,RH=50,PR1=21106.77,PB=1501,PF=1,PO=-7340,PR2=0.012545258
    meta_json = subprocess.check_output(
        ['exiftool', flir_image_path, '-Emissivity', '-SubjectDistance', '-AtmosphericTemperature',
         '-ReflectedApparentTemperature', '-IRWindowTemperature', '-IRWindowTransmission', '-RelativeHumidity',
         '-PlanckR1', '-PlanckB', '-PlanckF', '-PlanckO', '-PlanckR2', '-j'])
    meta = json.loads(meta_json)[0]

    # exifread can't extract the embedded thermal image, use exiftool instead
    thermal_img_bytes = subprocess.check_output(["exiftool", "-RawThermalImage", "-b", flir_image_path])
    thermal_img_stream = io.BytesIO(thermal_img_bytes)

    thermal_img = Image.open(thermal_img_stream)
    thermal_np = np.array(thermal_img)

    # fix endianness, the bytes in the embedded png are in the wrong order
    thermal_np = np.vectorize(lambda x: (x >> 8) + ((x & 0x00ff) << 8))(thermal_np)

    # raw values -> temperature
    raw2tempfunc = np.vectorize(lambda x: raw2temp(x, E=meta['Emissivity'], OD=_parse_length(meta['SubjectDistance']),
                                                   RTemp=_parse_temp(meta['ReflectedApparentTemperature']),
                                                   ATemp=_parse_temp(meta['AtmosphericTemperature']),
                                                   IRWTemp=_parse_temp(meta['IRWindowTemperature']),
                                                   IRT=meta['IRWindowTransmission'],
                                                   RH=_parse_percent(meta['RelativeHumidity']), PR1=meta['PlanckR1'],
                                                   PB=meta['PlanckB'], PF=meta['PlanckF'], PO=meta['PlanckO'],
                                                   PR2=meta['PlanckR2']))
    thermal_np = raw2tempfunc(thermal_np)

    return thermal_np


#obtains building list from the user and returns a dictionary structure with the
#key being the building name and the list within the key containing the building's
#height, latitude, and longitude as obtained from the Buildings.xlsx file
def building_names():
    input_building_list = list(line.strip('\n') for line in open('Building_Input.txt'))
    file = pd.read_excel("C:/Users/nayoung/Desktop/Test_Code/Buildings.xlsx")
    building_list = {}
    for index, building_input in enumerate(input_building_list):
        buildings = building_input.strip().title()
        if file['Building Name'].str.contains(buildings).any():
            for x in range(file.shape[0]):
                if buildings == file['Building Name'][x]:
                    if file.Height[x] == 0 or file.Latitude[x] == 0 or file.Longitude[x] == 0:
                        print('Error: fix values for the building information.')
                        print('Restart the Program.')
                        exit(0)
                    else:
                        building_list[buildings] = [file.Height[x], file.Latitude[x], file.Longitude[x]]
        else:
            print('%s not in list.' % buildings)
            print('Error: fix Building_Input.txt file.')
            print('Restart the Program.')
            exit(0)
    return building_list


# get_data_path_names() function does not work for pweave (to publish).
def get_data_path_names(): #Returns a list containing a list of paths to picture names and a list of GPS_data
    dir_path = os.path.dirname(os.path.realpath(__file__))	#Gets directory to the folder containing this file

    picture_folder_path = dir_path + r'\Pictures' #Gets file names in folder 'Pictures'
    picture_paths = [os.path.join(picture_folder_path,f) for f in os.listdir(picture_folder_path) if os.path.exists(os.path.join(picture_folder_path,f))]
    if len(picture_paths) < 1:
        sys.exit('Warning: No file found in the folder \'Pictures.\' Please add picture files before running the code again.\nExiting.')

    GPS_folder_path = dir_path + r'\GPS_Information' #Gets file names in folder 'GPS_Information'
    GPS_information_path = [os.path.join(GPS_folder_path,f) for f in os.listdir(GPS_folder_path) if os.path.exists(os.path.join(GPS_folder_path,f))]

    if len(GPS_information_path) < 1:
        sys.exit('Warning: No file found in the folder \'GPS_Information.\' Please add the GPS file before running the code again.\nExiting.')
    elif len(GPS_information_path) > 1:
        sys.exit('Warning: Multiple files found in the folder \'GPS_Information.\' Please ensure there is only one GPS file before running the code again.\nExiting.')

    return [picture_paths,GPS_information_path]


def get_gps_data(GPS_data_path): #Returns a list of each GPS point where each entry is a sublist containing Time(UTC), Latitude, Longitude, Altitude(cm above mean sea level), Velocity (mph)
    the_file = list(line.strip('\n') for line in open(GPS_data_path))
    GPS_data = []
    for index, gps_info in enumerate(the_file):
        gps_each = gps_info.split(' ')
        gps_each[1] = float(gps_each[1][0:2] + '.' + gps_each[1][2::])
        gps_each[2] = float(gps_each[2][0:4] + '.' + gps_each[2][4::])
        #print(gps_each)
        GPS_data.append(gps_each)
    return GPS_data


def get_ambient_temperature(GPS_Time): #Returns ambient temperature in Celsius as obtained from UC Davis' historical weather API
    #This is the beginning of the link to obtain the average temperature over a specified interval
    Request_Start_Info = 'https://ucd-pi-iis.ou.ad3.ucdavis.edu/piwebapi/streams/P09KoOKByvc0-uxyvoTV1UfQmxkAAAVVRJTC1QSS1QXEFJVElUNDA0NQ/summary?'

    Request_Time_Start_Str = str(GPS_Time)
    #Convert time into a time object
    Request_Time_Start_Time_Object = datetime.datetime.strptime(Request_Time_Start_Str, '%y%m%d%H%M%S')
    #
    Delta_Time_Num = 1
    Delta_Time_Str = str(Delta_Time_Num)
    Delta_Time_Type = 'm'  # minutes
    #Set end time as 1 minute after the start time to get the average temperature over one minute. This should be close to the actual temperature at the timethe picture was taken
    Request_Time_End_Time_Object = Request_Time_Start_Time_Object + datetime.timedelta(minutes=Delta_Time_Num)
    Request_Time_End = datetime.datetime.strftime(Request_Time_End_Time_Object, '%Y-%m-%dT%H:%M:%S')
    Request_End_Info = '&summarytype=Average&SummaryDuration=' + Delta_Time_Str + Delta_Time_Type

    Request_Time_Start_Str = datetime.datetime.strftime(Request_Time_Start_Time_Object, '%Y-%m-%dT%H:%M:%S')

#Merge API request pieces, the Z after the time strings represents the time zone UTC
    Request_Link = Request_Start_Info + 'startTime=' + Request_Time_Start_Str + 'Z' + '&endTime=' + Request_Time_End + 'Z' + Request_End_Info
#print(Request_Link)
    Night_Temp_Data = requests.get(Request_Link)
    Night_Temp_Value_F = Night_Temp_Data.json()['Items'][0]['Value']['Value']
    Night_Temp_Value_C = (Night_Temp_Value_F - 32) * 5 / 9
    return Night_Temp_Value_C


def get_mean_temperature(minr, maxr, minc, maxc, thermal_np, ambient_temperature):
    each_temp_list = []	#list for each hotspot pixel in cutout
    significant_delta_temp = 25 * 5 / 9
    for i in range(minr, maxr):
        for j in range(minc, maxc):
            if thermal_np[i][j] > (ambient_temperature + significant_delta_temp):
                each_temp_list.append(thermal_np[i][j])
    mean_temp = sum(each_temp_list) / len(each_temp_list)		#mean temp. calculation
    return mean_temp, each_temp_list

def hotspot_size(each_temp_list, pixel_area):
    hot_size = len(each_temp_list) * pixel_area		#hotspot size calculation	#add to dictionary of object size
    return hot_size




if __name__ == "__main__":
    #path_to_files = get_data_path_names()
    path_to_files = ['C:/Users/user_name/Desktop/Test_Code/Pictures/',
                     'C:/Users/user_name/Desktop/Test_Code/GPS_Information/']
    image_list = [f for f in listdir(path_to_files[0]) if isfile(join(path_to_files[0], f))]
    gps_list = [f for f in listdir(path_to_files[1]) if isfile(join(path_to_files[1], f))]
    gps_data = get_gps_data(path_to_files[1] + gps_list[-1])
    building_information = building_names()

    for index, key in enumerate(building_information.keys()):
        building_name = key

        for x in gps_data:
        #Determine the time and which picture is for this building by matching the GPS associated with the picture to the GPS associated with the building.
            if abs(building_information[key][1] - x[1]) < 0.000005 and abs(building_information[key][2] - x[2]) < 0.000005:
                picture_path = path_to_files[0] + image_list[gps_data.index(x)]
                time_picture_taken = x[0]
                drone_altitude = float(x[3])

        ambient_temperature = get_ambient_temperature(time_picture_taken)

        original_image = data.load(picture_path)
        thermal_np = extract_thermal(picture_path)

        if np.amax(thermal_np) <= ambient_temperature: # Skip the image if the maximum temperature is smaller or same as ambient
            fig, axes = plt.subplots(ncols = 2, nrows = 1, figsize = (12, 12))
            ax1, ax2 = axes.flat
            ax1.imshow(original_image)
            ax1.axis('off')
            ax2.axis('off')
            building_name += '\n'
            print_ambient = 'Ambient Temperature: %.2f C\n' % ambient_temperature
            txt = 'No hot object detected.'
            plt.text(0, 0.5, building_name + print_ambient + txt, fontsize=12)
            plt.show()
            continue


        significant_delta_temp = 25 * 5 / 9
        # This is the temperature above the ambient air temperature required to assume that an object is on. It is set to a delta of 25°F (delta of 13.89°C), but should be adjusted with more research.
        thermal_matrix = thermal_np.copy()
        thermal_matrix[thermal_matrix < (ambient_temperature + significant_delta_temp)] = 0
        thermal_matrix[thermal_matrix > (ambient_temperature + significant_delta_temp)] = 1
        edges_image = feature.canny(thermal_matrix, sigma = 1)
        label_image = label(edges_image)

        fig, axes = plt.subplots(ncols = 2, nrows = 1, figsize = (12, 12))
        ax1, ax2 = axes.flat
        ax1.imshow(original_image)
        ax1.axis('off')
        ax2.axis('off')
        minr_list, minc_list, maxr_list, maxc_list, area_list, rect_list, temp_list = [],[],[],[],[],[],[]
        building_height = float(building_information[key][0])
        distance = drone_altitude/100 - building_height*0.3048 - 52*0.3048 #Distance from drone to building top in meters

        if distance < 15:
            distance = 15

        x_pixel_len = 2 * distance * math.sin(41/2) / 320
        y_pixel_len = 2 * distance * math.sin(31/2) / 240
        pixel_area = x_pixel_len * y_pixel_len

        label_int = 0
        object_size = []

        for region in regionprops(label_image):
            minr, minc, maxr, maxc = region.bbox
            minr_o, minc_o, maxr_o, maxc_o = 4*minr, 4*minc, 4*maxr, 4*maxc
            rect_o = mpatches.Rectangle((minc_o, minr_o), (maxc_o - minc_o), (maxr_o - minr_o), fill = False, edgecolor = 'red', linewidth = 2)

            mean_temperature, each_temp_list = get_mean_temperature(minr, maxr, minc, maxc, thermal_np, ambient_temperature)
            size = hotspot_size(each_temp_list, pixel_area)
            area = (maxc - minc) * (maxr - minr) * 16 * pixel_area

            if 0.3 < area < 50:
                object_size.append(size)
                ax1.add_patch(rect_o)
                ax1.annotate('Spot' + str(label_int), xy = (minc_o, minr_o), color = 'white', fontsize = 10)

                minr_list.append(minr)
                minc_list.append(minc)
                maxr_list.append(maxr)
                maxc_list.append(maxc)
                area_list.append(area)
                rect_list.append(rect_o)
                temp_list.append(mean_temperature)

                label_int += 1


        txt = ''

        if len(area_list) == 0:
            txt += 'No hot object detected.'
            txt += 'The building is off.'
        else:
            for i in range(label_int):
                txt += 'Spot %d: Mean Temperature: %0.2f C \n''' \
                       '            Object Size: %0.2f m2 \n' % (i, temp_list[i], object_size[i])
            txt += 'The building is on.'

        building_name += '\n'
        print_ambient = 'Ambient Temperature: %.2f C\n' % ambient_temperature

        plt.text(0, 0.5, building_name + print_ambient + txt, fontsize = 10)
        plt.show()
