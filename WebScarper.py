from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re

# Set up Selenium WebDriver
driver = webdriver.Chrome()

# Navigate to the starting page
driver.get("https://yedionp.afeka.ac.il/yedion/fireflyweb.aspx?prgname=Enter_Search")
with open('courses.json', mode='w', encoding='utf-8') as file:
    courses_data = []
# Wait for the selection element and click on "מדעי המחשב"
wait = WebDriverWait(driver, 10)


select_element = wait.until(EC.element_to_be_clickable((By.ID, "R1C9")))

# Find the option for "מדעי המחשב" and click it
option = select_element.find_element(By.XPATH, ".//option[@value='11']")
option.click()
print("Selected 'מדעי המחשב'")

time.sleep(2)

show_courses_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='הצגת קורסים בתוכנית לימוד']")))

show_courses_button.click()
print("Clicked 'הצגת קורסים בתוכנית לימוד'")

time.sleep(2)

valueToSearch = "//input[@value='חפש תוכניות לימוד אפשריות למסלול' and @class='btn btn-primary rounded g-mb-12']"
# Wait for the page to load
wait.until(EC.presence_of_element_located(
    (By.XPATH, valueToSearch)))

# Click on the button "חפש תוכניות לימוד אפשריות למסלול"

search_program_button = driver.find_element(By.XPATH, valueToSearch)
search_program_button.click()
print("Clicked 'חפש תוכניות לימוד אפשריות למסלול'")

# Wait for the page to load (adjust sleep time as necessary)
time.sleep(1)

# Now we are at the page with the table containing program links
table = wait.until(
    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))

# Extract the links for courses (look for <a> elements with class 'btn btn-primary rounded g-mb-12')
links = driver.find_elements(By.XPATH, "//a[@class='btn btn-primary rounded g-mb-12']")

parent_row_index = 1
while True:
    parent_row_id = f"MyFather1000{parent_row_index}"
    parent_row_xpath = f"//div[@id='{parent_row_id}']"
    if parent_row_index == 6: # לומדה can be more abstract
        parent_row_index += 1
        continue
    try:
        parent_row = driver.find_element(By.XPATH, parent_row_xpath)
        course_subject = parent_row.find_elements(By.XPATH, ".//div")[0].text
        # Extract the course link
        course_link = parent_row.find_elements(By.XPATH, ".//div")[1].find_element(By.TAG_NAME, "a").get_attribute("href")
        print(f"Found course link: {course_link}")

        # Click the course link
        driver.get(course_link)
        print(f"Clicked the course link: {course_link}")

        # Wait for the page to load
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))

        child_row_index = 1
        while True:
            try:
                child_row_id = f"MyFather1000{child_row_index}"
                child_row_xpath = f"//div[@id='{child_row_id}']"

                child_row = driver.find_element(By.XPATH, child_row_xpath)
                course_name = child_row.find_elements(By.XPATH, ".//div")[1].text
                course_code = child_row.find_elements(By.XPATH, ".//div")[0].text

                # Find and click the button
                button = child_row.find_element(By.XPATH,
                                                ".//input[@value='חיפוש קורס במערכת השעות' and @tabindex='0']")
                button.click()
                print(f"Clicked button in row {child_row_id} for course: {course_name}")
                try:
                    popup_close_button = driver.find_element(By.XPATH,
                                                             "//button[@class='btn btn-secondary closefirstmodal' and @data-dismiss='modal']")
                    popup_close_button.click()
                    driver.back()
                    child_row_index += 1
                    time.sleep(2)
                    print("Closed the popup modal")
                    continue
                except Exception:
                    print("No popup detected")
                courses_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'Father')))
                GroupAndType_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'TextAlignRight')))

                courses = []
                for course, groupAndType in zip(courses_section, GroupAndType_section):
                    try:
                        htmlText = groupAndType.get_attribute('innerHTML')
                        # Regular expression patterns
                        course_type_pattern = r"(?<=קורס מסוג\s).*?(?=\s*&nbsp;)"
                        group_pattern = r"קבוצה : (\d+)"

                        # Extract course type
                        course_type_match = re.search(course_type_pattern, htmlText)
                        course_type = course_type_match.group(0) if course_type_match else None

                        # Extract group number
                        group_match = re.search(group_pattern, htmlText)
                        group_number = group_match.group(1) if group_match else None

                        print("Course Type:", course_type)
                        print("Group Number:", group_number)
                        semester = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][1]").text.split(":")[-1].strip()
                        day = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][2]").text.split(":")[
                            -1].strip()
                        start_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][3]").text
                        end_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][4]").text
                        try:
                            lecturer = course.find_element(By.XPATH,
                                                           ".//div[contains(@class, 'InRange')][5]//a").text.strip()
                        except Exception:
                            lecturer = "No Lecturer Yet"  # If the lecturer is not found, assign an empty string
                        room = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][6]").text.split(":")[
                            -1].strip()

                        courses.append({
                            "Course Subject": course_subject,
                            "Course Name": course_name,
                            "Course Code": course_code,
                            "Group Code": group_number,
                            "Lecture Type": course_type,
                            "Semester": semester,
                            "Day": day,
                            "StartTime": start_time,
                            "EndTime": end_time,
                            "Lecturer": lecturer,
                            "Room": room,
                        })
                    except Exception as e:
                        print(f"Error processing a course: {e}")

                courses_data.extend(courses)

                # Wait for the new page to load
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))

                driver.back()
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
                time.sleep(2)

                child_row_index += 1

            except Exception as e:
                print(f"No more child rows to process. Last processed child row index: {child_row_index - 1}")
                break

        driver.back()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
        time.sleep(5)

        parent_row_index += 1

    except Exception as e:
        print(f"No more parent rows to process. Last processed parent row index: {parent_row_index - 1}")
        break

# Write all extracted courses data to the JSON file
with open('courses.json', mode='w', encoding='utf-8') as file:
    json.dump(courses_data, file, ensure_ascii=False, indent=4)

# Close the browser
driver.quit()




# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import json
#
# # Set up Selenium WebDriver
# driver = webdriver.Chrome()
#
# # Navigate to the webpage
# driver.get("https://yedionp.afeka.ac.il/yedion/fireflyweb.aspx?prgname=S_SHOW_PROGS&arguments=-N2025,-N11009")  # Replace with the actual URL
#
# # Open JSON file for writing with UTF-8 encoding
# with open('coursesWorked.json', mode='w', encoding='utf-8') as file:
#     courses_data = []
#
#     # Wait for the table to load
#     wait = WebDriverWait(driver, 10)
#     table = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#
#     # Iterate through rows with IDs like MyFather10001, MyFather10002, etc.
#     row_index = 1
#     while True:
#         try:
#             # Construct the row ID dynamically
#             row_id = f"MyFather1000{row_index}"
#             row_xpath = f"//div[@id='{row_id}']"
#
#             # Find the row
#             row = driver.find_element(By.XPATH, row_xpath)
#
#             # Extract the course name (second div in the row)
#             course_name = row.find_elements(By.XPATH, ".//div")[1].text  # Adjusted index for the second div
#
#             # Find the button in the row
#             button = row.find_element(By.XPATH, ".//input[@value='חיפוש קורס במערכת השעות' and @tabindex='0']")
#
#             # Click the button
#             button.click()
#             print(f"Clicked button in row {row_id} for course: {course_name}")
#             courses_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'Father')))
#
#             # Extract course data
#             courses = []
#             for course in courses_section:
#                 try:
#                     semester = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][1]").text.split(":")[-1].strip()
#                     day = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][2]").text.split(":")[-1].strip()
#                     start_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][3]").text
#                     end_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][4]").text
#                     lecturer = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][5]//a").text.strip()
#                     room = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][6]").text.split(":")[-1].strip()
#
#                     # Append to the list
#                     courses.append({
#                         "Course Name": course_name,  # Add course name to the data
#                         "סמסטר": semester,
#                         "יום בשבוע": day,
#                         "שעת התחלה": start_time,
#                         "שעת סיום": end_time,
#                         "מרצה": lecturer,
#                         "חדר לימוד": room,
#                     })
#                 except Exception as e:
#                     print(f"Error processing a course: {e}")
#
#             # Append the courses to the main data list
#             courses_data.extend(courses)
#
#             # Wait for the new page to load if needed
#
#             # Navigate back to the previous page
#             driver.back()
#
#             # Wait for the table to reload (adjust if the page takes time to refresh)
#             wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#             time.sleep(2)  # Adjust the sleep duration if necessary
#
#             # Increment the index to check the next row
#             row_index += 1
#
#         except Exception as e:
#             # Break the loop if no more rows are found or another issue occurs
#             print(f"No more rows to process. Last processed row index: {row_index - 1}")
#             print(f"Error: {e}")
#             break
#
#     # Write all extracted courses data to the JSON file
#     json.dump(courses_data, file, ensure_ascii=False, indent=4)
#
# # Close the browser
# driver.quit()


