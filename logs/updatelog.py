import datetime

def checkforDB():
    logpath = "./logs/update_db.csv"
    if FileNotFoundError:
        with open(logpath, 'w') as file:
            file.write("ERDDAP_ID,AGOL_ID,seed_url,full_url,last_update\n")

def updateLog(ERDDAP_ID, AGOL_ID, seed_url, full_url,lastest_data, last_update) -> None:
    logpath = "./logs/update_db.csv"
    
    new_row = f"{ERDDAP_ID},{AGOL_ID},{seed_url},{full_url},{lastest_data},{last_update}\n"
    
    with open(logpath, 'a') as file:
        file.write(new_row)
    
    print("Log Updated")

def getTimefromID(itemID):
    logpath = "./logs/update_db.csv"
    
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
    logpath = "./logs/update_db.csv"
    
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

def updateCallFromID(itemID) -> list:
    logpath = "./logs/update_db.csv"
    updateParams = []
    with open(logpath, 'r') as file:
        lines = file.readlines()
        for line in lines[1:]:  
            columns = line.strip().split(",")
            print(f"\nChecking line: {line.strip()}")
            print(f"\nColumns: {columns}")
            if itemID == columns[1]: 
                updateParams = [columns[3], columns[4], columns[5]]
                print(f"\nMatch found. Returning Params: {updateParams}")
                return updateParams
    
    print("No match found.")
    return None

def get_current_time() -> str:
    return str(datetime.datetime.now().isoformat())