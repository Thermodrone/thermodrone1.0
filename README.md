# Thermodrone1.0
University of California, Davis. EME185 course: team Thermodrone1.0
This program was initiated and designed to assist analysing FLIR thermal images obtained by FLIR C2 of a building rooftop as a part of design project. This design specifically analyzes hot object over buildings or such locations that has potential of wasting energy of the location. Instructions are as follow.


# Servo
"OnlyOnTrigger.ino" is an arduino code to trigger a servo to automatically take image with FLIR C2 and record geographical information.
This is specific design that depends on speed. As the arduino detects slow down of the speed, it will trigger the servo to take image and record GPS data, such as date, time, altitude, longitude, latitude, and speed.


# Image Analysing Program (FLIR C2)
The code analyzes the thermal image based on its temperature. 

- Process

Before running the program, the user should have a folder of thermal images imported, a folder of GPS data, locations list with known geographical information in excel file, and input of excpected locations in text file. The program will initially read through input location (building) names and obtain its geographical information based on known location information list. Then it loads corresponding thermal image and analyze it.
The analyzation of the image consists of hot object indication, size of the object, and mean temperature of the object.


The program requires few modules in python:

Numpy       http://www.numpy.org/               pip install numpy

Scipy       https://www.scipy.org/              pip install scipy

Skimage     http://scikit-image.org/            pip install scikit_image

Opencv      https://opencv.org/                 pip install opencv_python

Pandas      https://pandas.pydata.org/          pip install pandas

Datetime    https://pypi.org/project/DateTime/  pip install datetime

Requests    https://pypi.org/project/requests/  pip install requests

Pweave      http://mpastell.com/pweave/         pip install pweave

Exiftool.exe  https://www.sno.phy.queensu.ca/~phil/exiftool/install.html  


Yet this code have only been tested with FLIR C2 images.

Extracting temperature embedded in a FLIR image credits to the following link:
https://github.com/Nervengift/read_thermal.py
