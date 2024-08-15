import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import erddap_client as ec
from src.erddap_client import ERDDAPHandler

class TestERDDAPHandler(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    # Testing updateObjectfromParams
    def test_updateObjectfromParams(self):
        tabledapDefaultTest = ec.tabledapDefault
        
        # Test parameters from ERDDAP documentation
        testParams = {
            "datasetid": "pmelTaoDySst",
            "fileType": "htmlTable",
            "station": "station",
            "wmo_platform_code": "wmo_platform_code",
            "start_time": "2015-05-23T12:00:00",
            "end_time": "2015-05-31T12:00:00"
        }
        
        # Update tabledapDefault with the test parameters
        ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)
        
        # Expected tabledapDefault object after updating with test parameters
        expected_tabledapDefault = ec.ERDDAPHandler(
            datasetid="pmelTaoDySst",
            fileType="htmlTable",
            longitude="longitude",
            latitude="latitude",
            time="time",
            station="station",
            wmo_platform_code="wmo_platform_code",
            start_time="2015-05-23T12:00:00",
            end_time="2015-05-31T12:00:00"
        )
        
        self.assertEqual(tabledapDefaultTest.__dict__, expected_tabledapDefault.__dict__)


    # UH OH: Using gcoos2 broke this test and now we know the sample URL is a lie.
    def test_generate_url(self):
        # Initialize tabledapDefault 
        tabledapDefaultTest = ec.tabledapDefault
        
        # Test parameters from ERDDAP documentation
        testParams = {
            "datasetid": "pmelTaoDySst",
            "fileType": "htmlTable",
            "start_time": "2015-05-23T12:00:00",
            "end_time": "2015-05-31T12:00:00"
        }
        
        #Calling the previous function we tested.
        ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)
        
        generated_url = tabledapDefaultTest.generate_url()
        
        # Expected URL based directly from documentation
        expected_url = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/pmelTaoDySst.htmlTable?longitude,latitude,time,station,wmo_platform_code,T_25&time%3E=2015-05-23T12:00:00Z&time%3C=2015-05-31T12:00:00Z"
        
        self.assertEqual(generated_url, expected_url)
    
    def test_generate_url2(self):
        # Initialize tabledapDefault 
        tabledapDefaultTest = ec.tabledapDefault
        
        # Test parameters from ERDDAP documentation
        testParams =  {
        "datasetid": "gcoos_42G01",
        "fileType": "json",
        "start_time": "2024-05-25T00:00:00",
        "end_time": "2024-05-28T00:00:00"
        }

        #Loading a few additional attributes to test with
        additionals = ["sea_surface_temperature_0", "sea_water_speed_0", "sea_water_direction_0", "upward_sea_water_velocity_0"]
        
        #Calling the previous function we tested (oops).
        ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)
        
        generated_url = tabledapDefaultTest.generate_url(additionals)
        
        # Expected URL based directly from documentation
        expected_url = "https://erddap2.gcoos.org/erddap/tabledap/gcoos_42G01.json?time%2Clatitude%2Clongitude%2Cplatform%2Ccrs%2Cdepth%2Csea_surface_temperature_0%2Csea_water_speed_0%2Csea_water_direction_0%2Cupward_sea_water_velocity_0&time%3E=2024-07-30T00%3A00%3A00Z&time%3C=2024-08-06T14%3A36%3A00Z"
        
        self.assertEqual(generated_url, expected_url)


if __name__ == '__main__':
    unittest.main()


#--------------------------------------------------------------------------------------------
#This test really doesn't do much, but I want to keep this here until the mystery of 42G01 is resolved.
# def test_return_response(self):
#     tabledapDefaultTest = ec.tabledapDefault
    
#     thetime = ec.ERDDAPHandler.get_current_time()
#     testParams = {
#     "datasetid": "gcoos_42G01",
#     "fileType": "geoJson",
#     "station": "42G01",
#     "wmo_platform_code": "42G01",
#     "start_time": "2023-05-25T03:00:00",
#     "end_time": thetime
#     }

#     tabledapDefaultTest.datasetid = testParams["datasetid"]
#     tabledapDefaultTest.filetype = testParams["fileType"]
#     tabledapDefaultTest.station = testParams["station"]
#     tabledapDefaultTest.wmo_platform_code = testParams["wmo_platform_code"]
#     tabledapDefaultTest.start_time = testParams["start_time"]
#     tabledapDefaultTest.end_time = testParams["end_time"]

#     generated_url = tabledapDefaultTest.generate_url()

#     response = ec.ERDDAPHandler.return_response(generated_url)

#     print(response["message"])
#--------------------------------------------------------------------------------------------