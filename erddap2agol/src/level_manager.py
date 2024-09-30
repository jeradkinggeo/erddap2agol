from . import erddap_client as ec
from . import das_client as dc
from . import ago_wrapper as aw

import sys, os, datetime
from datetime import timedelta, datetime

#This module will handle the logic for determining the level of detail in the data that is being processed



def movingWindow(isStr: bool):
    if isStr == True:
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        return start_time.isoformat(), end_time.isoformat()
    else:
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        return start_time, end_time

def checkDataRange(datasetid) -> bool:
    startDas, endDas = dc.convertFromUnixDT(dc.getTimeFromJson(datasetid))
    window_start, window_end = movingWindow(isStr=False)
    if startDas <= window_end and endDas >= window_start:
        return True
    else:
        return False  
    
