import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import erddap_client as ec
from src.erddap_client import ERDDAPHandler

class TestERDDAPHandler(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_generate_url(self):
        # Initialize tabledapDefault with default values
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
        tabledapDefaultTest.datasetid = testParams["datasetid"]
        tabledapDefaultTest.filetype = testParams["fileType"]
        tabledapDefaultTest.station = testParams["station"]
        tabledapDefaultTest.wmo_platform_code = testParams["wmo_platform_code"]
        tabledapDefaultTest.start_time = testParams["start_time"]
        tabledapDefaultTest.end_time = testParams["end_time"]
        
        # Generate the URL
        generated_url = tabledapDefaultTest.generate_url()
        print(f"Generated URL: {generated_url}")
        
        # Expected URL based on the test parameters
        expected_url = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/pmelTaoDySst.htmlTable?longitude,latitude,time,station,wmo_platform_code,T_25&time%3E=2015-05-23T12:00:00Z&time%3C=2015-05-31T12:00:00Z"
        
        # Assert that the generated URL matches the expected URL
        self.assertEqual(generated_url, expected_url)

if __name__ == '__main__':
    unittest.main()