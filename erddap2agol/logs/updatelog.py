import datetime
import os

def makeDBdir():
    agol_home = os.getenv('AGOL_HOME', '/arcgis/home')
    DBdir = os.path.join(agol_home, 'e2a_update_db')
    os.makedirs(DBdir, exist_ok=True)
    
    return DBdir

def checkforDB():
    logpath = makeDBdir()
    filepath = os.path.join(logpath, "update_db.csv")
    if not os.path.exists(filepath):
        with open(filepath, 'w') as file:
            file.write("ERDDAP_ID,AGOL_ID,seed_url,full_url,lastest_data,last_update,isNRT\n")
    return filepath


def updateLog(ERDDAP_ID, AGOL_ID, seed_url, full_url,lastest_data, last_update, isNRT) -> None:
    logpath = checkforDB()
    
    new_row = f"{ERDDAP_ID},{AGOL_ID},{seed_url},{full_url},{lastest_data},{last_update},{isNRT}\n"
    
    with open(logpath, 'a') as file:
        file.write(new_row)
    
    print("Log Updated")


def getTimefromID(itemID):
    logpath = checkforDB()
    
    with open(logpath, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:  # Skip the header line
            columns = line.strip().split(",")
            print(f"Checking line: {line.strip()}")
            print(f"Columns: {columns}")
            if itemID == columns[1]: 
                url = columns[3]  
                print(f"Match found. Returning URL: {url}")
                return url
    
    print("No match found.")
    return None
    
def getUrlFromID(itemID):
    logpath = checkforDB()
    
    with open(logpath, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:  # Skip the header line
            columns = line.strip().split(",")
            print(f"Checking line: {line.strip()}")
            print(f"Columns: {columns}")
            if itemID == columns[1]: 
                url = columns[3]  
                print(f"Match found. Returning URL: {url}")
                return url
    
    print("No match found.")
    return None

# Search the log for the itemID and return the update params 
def updateCallFromID(itemID) -> list:
    logpath = checkforDB()
    updateParams = []
    with open(logpath, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:  
            columns = line.strip().split(",")
            if itemID == columns[1]: 
                updateParams = [columns[3], columns[4], columns[5]]
                print(f"\nMatch found. Returning Params: {updateParams}")
                return updateParams
    
    print("No match found.")
    return None

# Search the log for the NRT items and return the itemIDs 
def updateCallFromNRT(boolPref) -> dict:
    logpath = checkforDB()
    nrt_dict = {} 
    
    with open(logpath, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:  # Skip header
            columns = line.strip().split(",")

            if str(boolPref) == columns[6].strip(): 
                nrt_dict[columns[0]] = columns[1]

    if nrt_dict:
        return nrt_dict
    else:
        print("No match found.")
        return {}

def get_current_time() -> str:
    return str(datetime.datetime.now().isoformat())