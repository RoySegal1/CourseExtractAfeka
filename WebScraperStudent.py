from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import re
import json


# Function to clean the grade value (get only the number after "ציון:")
def clean_grade(grade_text_in):
    match = re.search(r"ציון:\s*(\d+)", grade_text_in)
    return match.group(1) if match else "N/A"  # Return "N/A" if not found


def clean_nz(grade_text_in):
    credits_pattern = r"נ\"ז (\d+(\.\d+)?)"
    match = re.search(credits_pattern, grade_text_in)
    return match.group(1) if match else "N/A"  # Return "N/A" if not found


# Function to clean the course code (get only the number before the first non-digit character)
def clean_code(code_text_in):
    match = re.match(r"(\d+)", code_text_in)
    return match.group(1) if match else "N/A"  # Return "N/A" if not found


# Set up the WebDriver
driver = webdriver.Chrome()

try:
    # Navigate to the login page
    print("Opening login page...")
    driver.get("https://sso.afeka.ac.il/my.policy")
    time.sleep(2)  # Wait for the page to load

    # Find and fill the username/email field
    print("Filling username...")
    username_field = driver.find_element(By.NAME, "username")
    username_field.send_keys("Gilad.Tsfaty")

    # Find and fill the password field
    print("Filling password...")
    password_field = driver.find_element(By.NAME, "password")  # Replace with actual ID or selector
    password_field.send_keys("Last2025GT")

    # Submit the form (click the login button or press Enter)
    print("Clicking login button...")
    submit_button = driver.find_element(By.XPATH, "//input[@value='כניסה']")
    submit_button.click()

    # Wait for login to complete and the next page to load
    time.sleep(5)
    print("Logged in successfully!")

    print("Clicking Afeka-Net button...")
    afeka_net_button = driver.find_element(By.XPATH, "//span[@id='/Common/Yedion']")
    afeka_net_button.click()

    driver.switch_to.window(driver.window_handles[-1])  # Switch to the most recent tab

    # Perform actions on the website after login
    print("Clicking menu button...")
    # Wait for the element to be visible
    main_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//a[div/div[contains(text(), "רשימת ציונים")]]'))
    )
    main_button.click()
    # Wait for the dropdown to be present
    first_dropdown = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "R1C1"))
    )

    # Create a Select object
    select = Select(first_dropdown)

    # Select the option with value "-1" כל השנים
    select.select_by_value("-1")

    second_dropdown = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "R1C2"))
    )

    # Create a Select object
    select = Select(second_dropdown)

    # Select the option with value "0" שנתי
    select.select_by_value("0")

    # Wait for the button and click it
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick, \"SubmitForm\")]"))
    )
    button.click()

    # Wait for the main container div
    print("Waiting for the main container div...")
    try:
        main_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                                            "//div[contains(@class, 'col-md-12') and contains(@class, 'row') and contains(@class, 'NoPadding') and contains(@class, 'NoMarging')]"))
        )
        print("Main container found!")
    except Exception as e:
        print(f"Error: Failed to locate the main container - {e}")
        driver.quit()

    # Find all <details> elements inside the main container
    print("Finding all <details> elements inside the main container...")
    details_list = main_container.find_elements(By.TAG_NAME, "details")
    print(f"Found {len(details_list)} <details> elements.")

    # Store extracted data
    # Store extracted data
    results = {}

    # Assuming username will be retrieved via some method (hardcoded for now)
    username = "Roei.Segal"

    # Initialize the results for the user
    results["UserName"] = username
    results["Courses"] = []

    for index, details in enumerate(details_list):
        try:
            print(f"Processing details element {index + 1}/{len(details_list)}...")

            # Extract <h3> text from <summary>
            summary_element = details.find_element(By.TAG_NAME, "summary")
            h3_element = summary_element.find_element(By.TAG_NAME, "h3")
            summary_text = h3_element.text.strip()
            print(f"  Extracted summary: {summary_text}")

            # Find all divs with class 'Father' inside this <details>
            father_divs = details.find_elements(By.CLASS_NAME, "Father")
            print(f"  Found {len(father_divs)} 'Father' divs.")

            for f_index, father in enumerate(father_divs):
                print(f"    Checking 'Father' div {f_index + 1}/{len(father_divs)}...")

                # Check if there is a <div class="InRange"> containing "סופי-הרצאה"
                inrange_divs = father.find_elements(By.CLASS_NAME, "InRange")
                found_sofi = False
                nz_grade = ''
                for ir_index, inrange in enumerate(inrange_divs):
                    inrange_text = inrange.get_attribute("innerHTML").strip()
                    print(f"      InRange div {ir_index + 1}: '{inrange_text}'")
                    nz_temp = clean_nz(inrange_text)
                    if nz_temp != "N/A":
                        nz_grade = nz_temp
                    if "סופי-הרצאה" in inrange_text:
                        found_sofi = True
                        print(f"      Found 'סופי-הרצאה' in InRange div {ir_index + 1}/{len(inrange_divs)}.")

                        # Extract the grade from the <strong> element inside the div
                        try:
                            strong_div = father.find_element(By.XPATH, ".//div[strong]")
                            strong_element = strong_div.find_element(By.TAG_NAME, "strong")
                            grade_text = strong_element.get_attribute("innerHTML").strip()
                            print(grade_text)
                            grade = clean_grade(grade_text)
                            print(grade)
                            print(nz_grade)
                            # Extract the course code
                            code_div = father.find_element(By.CLASS_NAME, "pagetitle.InRange")
                            code_text = code_div.get_attribute("innerHTML").strip()
                            code = clean_code(code_text)

                            # Append to results
                            results["Courses"].append({code: [grade, nz_grade]})
                            print(f"      Extracted course: {code} | Grade: {grade}")
                        except Exception as e:
                            print(f"      Warning: <strong> element not found - {e}")
                        continue

                if not found_sofi:
                    print("      No 'סופי-הרצאה' found in this 'Father' div.")

        except Exception as e:
            print(f"Error processing details element {index + 1}: {e}")

    # Save results to a JSON file
    print("\nSaving results to JSON...")
    with open("courses_results_gilad.json", "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

    print("Results saved!")

finally:
    # Close the browser
    print("Closing browser...")
    driver.quit()
