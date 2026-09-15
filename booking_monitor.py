import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configuration
URL = "https://booking.bookinghound.cloud/fe/booking?og=bdffd003-ab61-4b27-8513-d0e8ef0f1425&mode=sl"
NTFY_TOPIC = "gorilla_trapeze" # CHANGE THIS to a unique, random string
CHECK_INTERVAL_SECONDS = 600 # Checks every 10 minutes

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
    # Set up a headless Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Checking URL: {URL}")
        driver.get(URL)
        
        # Wait 10 seconds to ensure the BookingHound widget fully loads
        time.sleep(10)
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        is_target_level = "Level 1" in page_text or "Level 2" in page_text
        has_places = False
        
        if is_target_level:
            
            # METHOD 1: Try to parse as a standard HTML table
            try:
                headers = driver.find_elements(By.XPATH, "//th")
                target_col_index = -1
                
                # Locate the index of the "Remaining Places" column
                for i, header in enumerate(headers):
                    if "Remaining Places" in header.text:
                        target_col_index = i + 1  # XPath uses 1-based indexing
                        break
                
                # If the column exists, check its cells for a number > 0
                if target_col_index != -1:
                    cells = driver.find_elements(By.XPATH, f"//tr/td[{target_col_index}]")
                    for cell in cells:
                        text_val = cell.text.strip()
                        if text_val.isdigit() and int(text_val) > 0:
                            has_places = True
                            break
            except Exception:
                pass # Silently fallback to Method 2

            # METHOD 2: Fallback to smart line-by-line parsing for CSS grids
            if not has_places and "Remaining Places" in page_text:
                # Selenium often extracts grid cells as standalone lines of text
                lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                
                for line in lines:
                    if line.isdigit():
                        num = int(line)
                        # If we find an isolated number between 1 and 99, 
                        # it is highly likely to be available spots (0 means sold out).
                        if 0 < num < 100:
                            has_places = True
                            break

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
        driver.quit()

if __name__ == "__main__":
    print("Starting single check for GitHub Actions...")
    while True:
        success = check_availability()
        
        if success:
            print("Availability found! Exiting script.")
            break  # FIX: Added break to prevent an infinite loop of push notifications
        else:
            print(f"Check complete. No places yet. Waiting {CHECK_INTERVAL_SECONDS}s before checking again.")
            time.sleep(CHECK_INTERVAL_SECONDS)
