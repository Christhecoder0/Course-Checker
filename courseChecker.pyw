from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv
import os
import time
import smtplib

with open("course_checker_log.txt", "a") as log:
    log.write(f"Program started at {datetime.now()}\n")

# Step 1: Set up WebDriver (use Chrome or Firefox)
options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)  # or webdriver.Firefox()
#driver.maximize_window()

# Step 2: Navigate to the USF search page
url = "https://usfweb.usf.edu/DSS/StaffScheduleSearch"
driver.get(url)

# Step 3: Fill out the form
def fill_form():
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "P_SEMESTER"))
        )
        # Select the term (e.g., Spring 2025)
        term_dropdown = Select(driver.find_element(By.ID, "P_SEMESTER"))
        term_dropdown.select_by_value("202505")

        # Select the campus (e.g., Tampa)
        campus_dropdown = Select(driver.find_element(By.ID, "P_CAMPUS"))
        campus_dropdown.select_by_value("T")

        # Select the department (e.g., Computer Science & Engineering)
        dept_dropdown = Select(driver.find_element(By.ID, "P_DEPT"))
        dept_dropdown.select_by_value("ESB")

        # Select the status 2 (e.g., Active)
        status2_dropdown = Select(driver.find_element(By.ID, "p_ssts_code"))
        status2_dropdown.select_by_value("A")

        # Select course level (e.g., Undergraduate)
        course_level_dropdown = Select(driver.find_element(By.ID, "P_CRSE_LEVL"))
        course_level_dropdown.select_by_value("UG")

        subject_input = driver.find_element(By.ID, "P_SUBJ")
        subject_input.clear
        subject_input.send_keys("COP")

        number_input = driver.find_element(By.ID, "P_NUM")
        number_input.clear
        number_input.send_keys("4710")
        # Select course attribute (e.g., Tampa Plan Approved Undergraduate)
        # attribute_dropdown = Select(driver.find_element(By.ID, "P_UGR"))
        # attribute_dropdown.select_by_value("TPAU")

        # Instructional Method: Check all boxes
        methods = ["p_insm_x_inad", "p_insm_x_incl", "p_insm_x_inhb", "p_insm_x_inpd", "p_insm_x_innl", "p_insm_x_inot"]
        for method in methods:
            checkbox = driver.find_element(By.ID, method)
            if not checkbox.is_selected():
                checkbox.click()

        # Session Date Details: Leave all checkboxes unchecked (default)
        # No action needed here as all are unchecked by default
    except Exception as e:
        print(f"An error occurred while filling out the form: {e}")


def submit():
    # Submit the form
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[value="Search"]'))
        )
    search_button.click()
    # Wait briefly to ensure the new tab opens
    time.sleep(2)  # Adjust this if necessary

    #     # Get the list of all open tabs
    #     tabs = driver.window_handles

    #     # Switch to the new tab (usually the last one in the list)
    #     driver.switch_to.window(tabs[-1])

    #     # Optionally, wait for the results table to load in the new tab
    #     try:
    #         results_table = WebDriverWait(driver, 10).until(
    #             EC.presence_of_element_located((By.ID, "results"))
    #         )
    #         print("Results table found!")
    #     except Exception as e:
    #         print(f"An error occurred: {e}")

    #     # Check the page source or extract results
    #     # print(driver.page_source)
    #     # WebDriverWait(driver, 10).until(
    #     #     EC.presence_of_element_located((By.ID, "results"))
    #     # )


# Step 4: Extract results from the table
def extract_results(x):
    try:
        # Switch to the results tab
        tabs = driver.window_handles
        driver.switch_to.window(tabs[-1])

        # Locate the results table
        results_table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "results"))
        )
        print("Results table found!")

        table = driver.find_element(By.ID, "results")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Parse rows
        i = 0
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if columns:
                crn = columns[3].text.strip()  # Adjust index for CRN
                seats_remain = columns[12].text.strip()  # Adjust index for seats remaining
                if(x >= 2):
                    return "53722"
                    crns = ["53722"]
                else:
                    crns = ["53722"]
                if (crn in crns):
                    i += 1
                    if int(seats_remain) > 0:
                        print(f"A seat is available for CRN {crn}!")
                        return crn  # Stop checking
                    else:
                        print(f"No seats available yet for CRN {crn}")
                        if i == len(crns):
                            return ""
        return ""

    except Exception as e:
        print(f"An error occurred while extracting results: {e}")

    finally:
        # Ensure the results tab is closed and switch back to the main tab
        driver.close()  # Close the results tab
        driver.switch_to.window(driver.window_handles[0])  # Switch back to the main tab

    return ""  # Continue checking

def send_notification(crn):
    # Load environment variables from the .env file
    load_dotenv()

    # Access environment variables
    sender_email = os.getenv("EMAIL")  # You can send it to yourself or others
    password = os.getenv("PASSWORD")  # Use an app-specific password if needed
    receiver_email = "chriswjroberts23@gmail.com"  

    message = MIMEText(f"A seat has opened up for CRN {crn}! Check your registration portal now!")
    message['Subject'] = "Seat Available Notification"
    message['From'] = sender_email
    message['To'] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


# Step 5: Run the automation
notFound = True

with open("running_flag.txt", "w") as f:
    f.write("Program is currently running...")
try:
    fill_form()
    x = 0
    crn = ""
    running = True
    # Create a filename based on the current date and time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"course_checker_log_{timestamp}.txt"
    # When you want to log the message
    with open(filename, "a") as log:
        while(running):
            if os.path.exists("stop.txt"):
                log.write("Stop file detected. Quitting.")
                running = False
                break
            while(crn == ""):
                submit()
                crn = extract_results(x)
                time.sleep(2)
                x += 1
                if(crn != ""):
                    log.write(f"[{time.ctime()}] A seat is available for CRN {crn}!\n")
                else:
                    log.write(f"[{time.ctime()}] No seats available yet for CRN {crn}!\n")
            if(running):
                send_notification(crn)
            running = False
finally:
    os.remove("running_flag.txt")
    with open("finished_running.txt", "w") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d: %H-%M-%S")
        f.write(f"Program finished at {timestamp}")
    driver.quit()
