import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configuration
URL = "https://booking.bookinghound.cloud/fe/booking?og=bdffd003-ab61-4b27-8513-d0e8ef0f1425&mode=sl"
NTFY_TOPIC = "trapeze" # CHANGE THIS to a unique, random string
CHECK_INTERVAL_SECONDS = 600 # Checks every 5 minutes

def send_push_notification(message):
    """Sends a push notification to your phone via the free ntfy.sh app"""
    try:
        requests.post(f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode(encoding='utf-8'),
            headers={
                "Title": "Booking Availability Alert!",
                "Priority": "urgent",
                "Tags": "tada,partying_face"
            })
        print("Push notification sent successfully.")
    except Exception as e:
        print(f"Failed to send notification: {e}")

def check_availability():
    # Set up a headless Chrome browser (runs in the background)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize the browser
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Checking URL: {URL}")
        driver.get(URL)
        
        # Wait 10 seconds to ensure the BookingHound widget fully loads via JavaScript
        time.sleep(10)
        
        # Extract all visible text from the loaded page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # ---------------------------------------------------------
        # PARSING LOGIC:
        # We check if Level 1 or Level 2 is on the page, AND look 
        # for a "Remaining Places" number that is greater than 0.
        # ---------------------------------------------------------
        
        is_target_level = "Level 1" in page_text or "Level 2" in page_text
        
        # This regex looks for "Remaining Places: " followed by any number from 1 to 99.
        # It ensures it doesn't match "Remaining Places: 0"
        has_places = re.search(r'Remaining Places:\s*[1-9][0-9]*', page_text, re.IGNORECASE)

        if is_target_level and has_places:
            print("Availability found!")
            send_push_notification("Spaces are now available for Level 1 or Level 2! Click to book: " + URL)
            return True
        else:
            print("No places available yet.")
            return False

    except Exception as e:
        print(f"An error occurred while checking: {e}")
        return False
    finally:
        # Always close the browser to free up memory
        driver.quit()

if __name__ == "__main__":
    print("Starting booking monitor...")
    while True:
        success = check_availability()
        
        if success:
            # Stop checking once we find availability so we don't spam your phone
            print("Exiting script. Go book your class!")
            break
            
        print(f"Waiting {CHECK_INTERVAL_SECONDS / 60} minutes before next check...\n")
        time.sleep(CHECK_INTERVAL_SECONDS)
