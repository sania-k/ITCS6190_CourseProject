# Data ingestion script placeholder
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType, IntegerType, FloatType, ArrayType, StructType, StructField, MapType

import time
from bs4 import BeautifulSoup
from datetime import datetime
import re
import requests

# Function to look up ICAO code by its ID using an API
# TODO: see if there is a more consistent way to do this
def get_icao_by_id(airport_code):
    if not airport_code:
        return None
    try:
        url = f"https://airportsapi.com/api/airports?filter%5Bcode%5D={airport_code.upper()}"
        headers = {'Accept': 'application/json'}

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json().get('data', [])

        if not data: 
            print(f"No airport found with name '{airport_code}'") 
            return None 
        
        airport_obj = data[0]['attributes'] 
        icao_code = airport_obj.get('icao_code') 

        if not icao_code: 
            print(f"ICAO code not available for '{airport_code}'") 
            return None 
           
        return icao_code
    
    except Exception:
        return None


# Function to look up ICAO code by its name using an API
# TODO: see if there is a more consistent way to do this
def get_icao_by_name(airport_name): 
    url = f"https://airportsapi.com/api/airports?filter%5Bname%5D={airport_name.replace(' ', '+')}" 
    headers = {'Accept': 'application/json'} 
    
    response = requests.get(url, headers=headers) 
    response.raise_for_status() 

    data = response.json().get('data', []) 

    if not data: 
        print(f"No airport found with name '{airport_name}'") 
        return None 

    airport_obj = data[0]['attributes'] 
    icao_code = airport_obj.get('icao_code') 
    
    if not icao_code: 
        print(f"ICAO code not available for '{airport_name}'") 
        return None 
    
    return icao_code


# Generates url for metar api call based on where and when
def gen_url(icao_code,date):
    base = "https://flightsupport24.com/map/archive.php?"

    month, day, year = date.split("/")

    request_URL = base + "station=" + icao_code + "&data=metar" + \
        "&year1="+ year + "&month1=" + month + "&day1=" + day + \
        "&year2="+year+"&month2="+ month+"&day2="+day+ \
        "&tz=Etc/UTC&format=onlytdf&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=2"

    return request_URL
    
# METAR data scraping -- makes api call 
def get_metar_data(icao_code, departureDate, departureTime):
    url = gen_url(icao_code, departureDate)

    try:
        res = requests.get(url).text
        mtr_data = res.strip().splitlines()[1:]        

         # Convert target time to minutes since midnight
        target_dt = datetime.strptime(departureTime, "%H:%M")
        target_minutes = target_dt.hour * 60 + target_dt.minute

        best_row = None
        smallest_diff = None

        for row in mtr_data:
            parts = row.split()
            if len(parts) < 3:
                continue

            row_time_str = parts[2]  # the time of the observation

            try:
                row_dt = datetime.strptime(row_time_str, "%H:%M")
                row_minutes = row_dt.hour * 60 + row_dt.minute
            except ValueError:
                continue

            if row_minutes <= target_minutes:
                diff = target_minutes - row_minutes
                if smallest_diff is None or diff < smallest_diff:
                    smallest_diff = diff
                    best_row = row

        return best_row or None
        
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None

    print("get metar data on",planeDate)
    if not icao_code:
        return None

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)

    driver.get("https://flightsupport24.com/map/#/metar-archive")
    wait = WebDriverWait(driver, 20)
    try:
        station_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Enter stations']"))
        )
        # Fill out the airport code
        station_input.send_keys(icao_code) 

        # Fill out the date to the day of the flight
        date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        date_inputs[0].send_keys(planeDate)
        date_inputs[1].send_keys(planeDate)

        # Submit form
        driver.find_element(By.CSS_SELECTOR, "span.anticon-search").click()
        time.sleep(10)  # wait for results to load

        # Grab the result
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        pre_tag = soup.find("pre") 
        if not pre_tag:
            return None
        
        text = pre_tag.get_text().strip()
        rows = text.splitlines()[1:]  # skip header
        if not rows:
            return None

        # Go line by line and find the closest to departure time
        target_dt = datetime.strptime(planeTime, "%H:%M")
        target_minutes = target_dt.hour * 60 + target_dt.minute

        best_row = None
        smallest_diff = None
        for row in rows:
            parts = row.split()
            if len(parts) < 3:
                continue
            row_time_str = parts[2]
            try:
                row_dt = datetime.strptime(row_time_str, "%H:%M")
                row_minutes = row_dt.hour * 60 + row_dt.minute
            except ValueError:
                continue
            if row_minutes <= target_minutes:
                diff = target_minutes - row_minutes
                if smallest_diff is None or diff < smallest_diff:
                    smallest_diff = diff
                    best_row = row

        # If no row was found before target time, default to the first row
        if best_row is None and rows:
            best_row = rows[0]
    finally:    
        driver.quit()
        return best_row
    

# Converts METAR string into JSON-like dictionary
def metar_to_json(metar_str):
    if not metar_str:
        return {}

    tokens = metar_str.split()
    result = {}

    # Sanity check: METAR should have at least station, date, time
    if len(tokens) < 3:
        return result

    i = 2  # Skip station and date tokens

   # Sanity check: METAR should have at least station, date, time
    if len(tokens) < 3:
        return result

    i = 2  # Skip station and date tokens
    if i >= len(tokens):
        return result

    # --- WIND DATA ---
    token = tokens[i]
    if "KT" in token:
        wind_match = re.match(r"(\d{3})(\d{2})(G(\d+))?KT", token)
        if wind_match:
            result["Wind_Direction_deg"] = int(wind_match.group(1))
            result["Wind_Speed_kt"] = int(wind_match.group(2))
            if wind_match.group(4):
                result["Wind_Gust_kt"] = int(wind_match.group(4))
        i += 1

    # --- VARIABLE WIND (ex/ 180V240) ---
    if i < len(tokens) and "V" in tokens[i]:
        i += 1

    # --- VISIBILITY (ends with SM) ---
    if i < len(tokens) and "SM" in tokens[i]:
        vis_match = re.match(r"(\d+(?:\s*\d/\d)?)SM", tokens[i])
        if vis_match:
            result["Visibility_SM"] = vis_match.group(1)
        i += 1

    # skip runway visual range
    if i < len(tokens) and "/" in tokens[i] and not re.match(r'^(M?\d{1,2})/(M?\d{1,2})$', tokens[i]):
        i += 1


    # --- WEATHER PHENOMENA ---
    weather_dict = {
        "RA": "rain", "SN": "snow", "UP": "unknown_precip",
        "FG": "fog", "FZFG": "freezing_fog", "BR": "mist",
        "HZ": "haze", "SQ": "squall", "FC": "funnel_cloud",
        "TS": "thunderstorm", "GR": "hail", "GS": "small_hail",
        "FZRA": "freezing_rain", "VA": "volcanic_ash"
    }

    weather_phenomena = []
    while i < len(tokens) and not any(char.isdigit() for char in tokens[i]):
        code = tokens[i]
        intensity = "moderate"

        if code.startswith("-"):
            intensity, code = "light", code[1:]
        elif code.startswith("+"):
            intensity, code = "heavy", code[1:]

        if code in weather_dict:
            weather_phenomena.append({
                "Type": weather_dict[code],
                "Intensity": intensity
            })
        else:
            break

        i += 1
        if len(weather_phenomena) >= 3:
            break

    if weather_phenomena:
        result["Weather_Phenomena"] = weather_phenomena

    # --- SKY CONDITION ---
    sky_dict = {
        "CLR": "no clouds below 12,000 ft",
        "FEW": "few clouds",
        "SCT": "scattered clouds",
        "BKN": "broken clouds",
        "OVC": "overcast"
    }

    sky_conditions = []
    while i < len(tokens) and re.match(r'^(CLR|FEW|SCT|BKN|OVC)\d{0,3}$', tokens[i]):
        match = re.match(r'^(CLR|FEW|SCT|BKN|OVC)(\d{3})?$', tokens[i])
        if match:
            amount, height = match.groups()
            height_ft = int(height) * 100 if height else None
            sky_conditions.append({
                "Cloud_Amount": sky_dict.get(amount, "unknown"),
                "Cloud_Height_ft": height_ft
            })
        i += 1

    if sky_conditions:
        result["Sky_Condition"] = sky_conditions

    # --- TEMPERATURE / DEW POINT ---
    if i < len(tokens) and "/" in tokens[i]:
        temp_match = re.match(r'^(M?\d{1,2})/(M?\d{1,2})$', tokens[i])
        if temp_match:
            temp_str, dew_str = temp_match.groups()

            def parse_temp(t):
                return -int(t[1:]) if t.startswith("M") else int(t)

            result["Temperature_C"] = parse_temp(temp_str)
            result["Dewpoint_C"] = parse_temp(dew_str)
        i += 1

    return result

# TODO: connect everything into one table
def main():
    # Testing METAR scraping works
    airport = "CLT"
    planeDate = "10/01/2025"
    planeTime = "08:00" 

    metar = get_metar_data(airport, planeDate, planeTime)
    if metar:
        print(metar)
    else:
        print("No METAR data returned.")
    
    json = metar_to_json(metar)
    print(json)

    # Loading flight data sample
    spark=SparkSession.builder.appName("testing").getOrCreate()

    airplane_df = spark.read.csv("flight_delay_jan2025.csv", header=True, inferSchema=True) # TODO: define schema
    airplane_df.createOrReplaceTempView("flight_delay")
    spark.sql("SELECT * FROM flight_delay").show()


    spark.stop()


if __name__ == "__main__":
    main()
