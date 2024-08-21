def checkforDB():
    logpath = "./logs/update_db.csv"
    if FileNotFoundError:
        with open(logpath, 'w') as file:
            file.write("ERDDAP_ID,AGOL_ID,seed_url,full_url,last_update\n")

def updateLog(ERDDAP_ID, AGOL_ID, seed_url, full_url, last_update) -> None:
    logpath = "./logs/update_db.csv"
    
    new_row = f"{ERDDAP_ID},{AGOL_ID},{seed_url},{full_url},{last_update}\n"
    
    with open(logpath, 'a') as file:
        file.write(new_row)
    
    print("Log Updated")

def getLastUrl():
    logpath = "./logs/update_db.csv"
    with open(logpath, 'r') as file:
        lines = file.readlines()
        last_line = lines[-1]
        url = last_line.split(",")[3]
        return url
    
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