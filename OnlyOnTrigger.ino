// The objective of this code is to program an arduino nano to trigger a servo when a drone it is attached to
// when the drone stops and to record the location of where the drone is.


// This code requires the downloading the following libraries

// 1. ServoTimer2 available at https://github.com/nabontra/ServoTimer2
// 2. NeoGPS  available at https://github.com/SlashDevin/NeoGPS



// the following libraries are used in the code

// used to trigger the servo
#include <ServoTimer2.h>

// used to store the gps data collected
#include <SPI.h>
#include <SD.h>

// used to collect gps data
#include <NMEAGPS.h>


// Creating objects necessary.
File myFile; // File objects are used to write to the sd card
ServoTimer2 myServo; // Servo objects are used to trigger the servo


int tookPic = 0; // counter variable used for logic later. keeps track of when the photo has been taken

long rLat = 0; // the latitude as a 10 decimal integer
long rLong = 0; // the longitude as a 10 decimal integer
long rAlt = 0; // the altitude in cm
float rVel = 0; // the velocity of the drone in MPH
String saveString; // string that is used to save files with different names. It is not used in the final system, but may be useful for future iterations
String timeString; // full time string that will be stored on the gps

String yearString; // string for what year it is
String monthString; // string for what month it is
String dateString; // string for the date
String hourString; // string for the hour.
String minuteString; // stirng for the minute
String secondString; // string for the second

// the following are comments are the comments that are used in the example for the NEOGPS library.
// they are useful comments for future iterations, but not interesting for the functionallity of the current system
// NOTE: Most of the lines of code within the comments are necessary for the code to run

//======================================================================
//  Program: NMEA.ino
//
//  Description:  This program uses the fix-oriented methods available() and
//    read() to handle complete fix structures.
//
//    When the last character of the LAST_SENTENCE_IN_INTERVAL (see NMEAGPS_cfg.h)
//    is decoded, a completed fix structure becomes available and is returned
//    from read().  The new fix is saved the 'fix' structure, and can be used
//    anywhere, at any time.
//
//    If no messages are enabled in NMEAGPS_cfg.h, or
//    no 'gps_fix' members are enabled in GPSfix_cfg.h, no information will be
//    parsed, copied or printed.
//
//  Prerequisites:
//     1) Your GPS device has been correctly powered.
//          Be careful when connecting 3.3V devices.
//     2) Your GPS device is correctly connected to an Arduino serial port.
//          See GPSport.h for the default connections.
//     3) You know the default baud rate of your GPS device.
//          If 9600 does not work, use NMEAdiagnostic.ino to
//          scan for the correct baud rate.
//     4) LAST_SENTENCE_IN_INTERVAL is defined to be the sentence that is
//          sent *last* in each update interval (usually once per second).
//          The default is NMEAGPS::NMEA_RMC (see NMEAGPS_cfg.h).  Other
//          programs may need to use the sentence identified by NMEAorder.ino.
//     5) NMEAGPS_RECOGNIZE_ALL is defined in NMEAGPS_cfg.h
//
//  'Serial' is for debug output to the Serial Monitor window.
//
//  License:
//    Copyright (C) 2014-2017, SlashDevin
//
//    This file is part of NeoGPS
//
//    NeoGPS is free software: you can redistribute it and/or modify
//    it under the terms of the GNU General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    NeoGPS is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with NeoGPS.  If not, see <http://www.gnu.org/licenses/>.
//
//======================================================================

//-------------------------------------------------------------------------
//  The GPSport.h include file tries to choose a default serial port
//  for the GPS device.  If you know which serial port you want to use,
//  edit the GPSport.h file.

#include <GPSport.h>

//------------------------------------------------------------
// For the NeoGPS example programs, "Streamers" is common set
//   of printing and formatting routines for GPS data, in a
//   Comma-Separated Values text format (aka CSV).  The CSV
//   data will be printed to the "debug output device".
// If you don't need these formatters, simply delete this section.

#include <Streamers.h>

//------------------------------------------------------------
// This object parses received characters
//   into the gps.fix() data structure

static NMEAGPS  gps;

//------------------------------------------------------------
//  Define a set of GPS fix information.  It will
//  hold on to the various pieces as they are received from
//  an RMC sentence.  It can be used anywhere in your sketch.

static gps_fix  fix;

//----------------------------------------------------------------
//  This function gets called about once per second, during the GPS
//  quiet time.  It's the best place to do anything that might take
//  a while: print a bunch of things, write to SD, send an SMS, etc.
//
//  By doing the "hard" work during the quiet time, the CPU can get back to
//  reading the GPS chars as they come in, so that no chars are lost.


// The following is relevant to the project.

static void doSomeWork()
{
  trace_all( DEBUG_PORT, gps, fix ); // useful for debugging. this displays the gps data on the monitor

  
  rLat = fix.latitudeL(); // latitude read from the gps. the data is an integer 
   rLong = fix.longitudeL(); // longitude read from the gps. the data is an integer
   rAlt = fix.altitude_cm(); // altitude in centimeters Note it is not the altitude from mean sea level. it is something else
  
  rVel = fix.speed_mph();
  // gets the data for the time. all the data are integers
    int rYear = fix.dateTime.year; 
    int rMonth = fix.dateTime.month;
    int rDate = fix.dateTime.date;
    int rHour = fix.dateTime.hours;
    int rMin = fix.dateTime.minutes;
    int rSec = fix.dateTime.seconds;
//

    String zString = String(0); // a string that is just zero. this is useful because for the final value, all the time strings must be 2 digits.

// casts all the integer data for time into strings so I can add them together for the file saving
    String yearString = String(rYear);


    // the following code segments cast the integer time data colleted to strings so they can be concatonated into one long string to be read by the analysis program
    if (rMonth < 10)
    {
    String monthStr = String(rMonth);
    monthString = zString + monthStr;
    }
    else
    {
    monthString = String(rMonth);
    }
    
    if (rDate < 10)
    {
      String dateStr = String(rDate);
     dateString = zString + dateStr;
    }
    else
    {
      dateString = String(rDate);
    }

    if (rHour < 10)
    {
      String hourStr = String(rHour);
      hourString = zString + hourStr;
    }
    else
    {
       hourString = String(rHour);
    }

    if (rMin < 10)
    {
      String minStr = String (rMin);
       minuteString = zString + minStr;
    }
    else
    {
      minuteString = String(rMin);
    }

    if (rSec < 10)
    {
      String secondStr = String(rSec);
       secondString = zString + secondStr;
    }
    else
    {
      secondString = String(rSec);
    }

    
// slaps everything together into a save file. this is useful for keeping track of when data was collected for future iterations, but again, it is not used in the Spring 2018 version
     saveString = yearString + monthString + dateString + hourString;

    // the detailed info for when the picture was taken
     timeString = saveString + minuteString + secondString;

  String SAVESTRING = String("gpsData"); // final save string that is acutally used in the program


// this part of the code determines if the camera should be triggered and stores the info if so

// if the drone is moving less than 2 mph and is higher than 3 cm above sea level, check to see if the drone has already taken a picture
// if the drone has not taken a picture yet, take a picture and record the data when it takes the picture.
// if the drone has taken a picture, do not take another picture. 
    if((rVel < 2) && (rAlt > 3))
    {
      if (tookPic < 2)
      {
        myServo.write(1700); // triggers the servo
        tookPic = 3;
        myFile = SD.open(SAVESTRING, FILE_WRITE); // opens the file to save to in the SD card
    myFile.print(timeString); // saves the time to the file
    myFile.print(' '); // makes a space between relevant data
    myFile.print(rLat); // saves the Latitude
    myFile.print(' ');
    myFile.print(rLong); // saves the longitude
    myFile.print(' ');
    myFile.print(rAlt); // saves the altitude
    myFile.print(' '); 
    myFile.println(rVel); // saves the velocity in mph

    myFile.close(); // closes the file
      }
      else
      {
        myServo.write(1000); // tells the servo to retract
      }
    }
    else
    {
      tookPic = 0; // resets the drone to take a picture again because the drone is moving quickly
      myServo.write(1000); // retracts the servo
    }
}

//------------------------------------
//  This is the main GPS parsing loop.

// the gps parsing loop says as long as the gps is available, read the data. gps fixes don't collect all the data at once.
// gps rely on a fix, which is like a running serial connection that is constantly feeding data.
// every second, doSomeWork is activated and does all the instructions inside that function.
// in between the time the function doSomeWork is active, the gps is constantly collecting data.
// that is why everything that takes more than a few clock cycles of the microcontroller is in doSomeWork
static void GPSloop()
{
  while (gps.available( gpsPort )) {
    fix = gps.read();
    doSomeWork();
  }

} // GPSloop

//--------------------------


// below is the setup function for the code. most of the setup is to configure the gps output to a serial monitor
// the serial monitor is not used for anything but debugging.
// the important code segments start on at the comment that says
// "Start of custom code" 
void setup()
{
  DEBUG_PORT.begin(9600);
  while (!DEBUG_PORT)
    ;

  DEBUG_PORT.print( F("NMEA.INO: started\n") );
  DEBUG_PORT.print( F("  fix object size = ") );
  DEBUG_PORT.println( sizeof(gps.fix()) );
  DEBUG_PORT.print( F("  gps object size = ") );
  DEBUG_PORT.println( sizeof(gps) );
  DEBUG_PORT.println( F("Looking for GPS device on " GPS_PORT_NAME) );

  #ifndef NMEAGPS_RECOGNIZE_ALL
    #error You must define NMEAGPS_RECOGNIZE_ALL in NMEAGPS_cfg.h!
  #endif

  #ifdef NMEAGPS_INTERRUPT_PROCESSING
    #error You must *NOT* define NMEAGPS_INTERRUPT_PROCESSING in NMEAGPS_cfg.h!
  #endif

  #if !defined( NMEAGPS_PARSE_GGA ) & !defined( NMEAGPS_PARSE_GLL ) & \
      !defined( NMEAGPS_PARSE_GSA ) & !defined( NMEAGPS_PARSE_GSV ) & \
      !defined( NMEAGPS_PARSE_RMC ) & !defined( NMEAGPS_PARSE_VTG ) & \
      !defined( NMEAGPS_PARSE_ZDA ) & !defined( NMEAGPS_PARSE_GST )

    DEBUG_PORT.println( F("\nWARNING: No NMEA sentences are enabled: no fix data will be displayed.") );

  #else
    if (gps.merging == NMEAGPS::NO_MERGING) {
      DEBUG_PORT.print  ( F("\nWARNING: displaying data from ") );
      DEBUG_PORT.print  ( gps.string_for( LAST_SENTENCE_IN_INTERVAL ) );
      DEBUG_PORT.print  ( F(" sentences ONLY, and only if ") );
      DEBUG_PORT.print  ( gps.string_for( LAST_SENTENCE_IN_INTERVAL ) );
      DEBUG_PORT.println( F(" is enabled.\n"
                            "  Other sentences may be parsed, but their data will not be displayed.") );
    }
  #endif

  DEBUG_PORT.print  ( F("\nGPS quiet time is assumed to begin after a ") );
  DEBUG_PORT.print  ( gps.string_for( LAST_SENTENCE_IN_INTERVAL ) );
  DEBUG_PORT.println( F(" sentence is received.\n"
                        "  You should confirm this with NMEAorder.ino\n") );

  trace_header( DEBUG_PORT );
  DEBUG_PORT.flush();

  gpsPort.begin( 9600 );

  // Start of custom code
  SD.begin(4); // starts communication with the SD card
 
  myServo.attach(6); // Tells the servo object assigned earlier to output on pin 6
  
}

//--------------------------


// main loop

// all useful code should be put in the function "doSomeWork" to avoid missing gps fix characters.
void loop()
{
  GPSloop(); 
  
}
