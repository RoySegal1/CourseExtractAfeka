from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import consts




def setup_driver():
    """Initialize and return the WebDriver"""
    driver = webdriver.Chrome()
    return driver


def create_wait(driver, timeout=10):
    """Create and return a WebDriverWait object"""
    return WebDriverWait(driver, timeout)


def navigate_to_course_search(driver, wait, program):
    """Navigate to the initial course search page"""
    driver.get("https://yedionp.afeka.ac.il/yedion/fireflyweb.aspx?prgname=Enter_Search")

    # Select computer science department
    xpath_value_to_select = f".//option[@value='{consts.study_programs[program]}']"
    select_element = wait.until(EC.element_to_be_clickable((By.ID, "R1C9")))
    option = select_element.find_element(By.XPATH, xpath_value_to_select)
    option.click()
    print("Selected 'מדעי המחשב'")

    # Click to show courses
    show_courses_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@value='הצגת קורסים בתוכנית לימוד']")))
    show_courses_button.click()
    print("Clicked 'הצגת קורסים בתוכנית לימוד'")

    # Wait for search button and click it
    value_to_search = "//input[@value='חפש תוכניות לימוד אפשריות למסלול' and @class='btn btn-primary rounded g-mb-12']"
    wait.until(EC.presence_of_element_located((By.XPATH, value_to_search)))
    search_program_button = driver.find_element(By.XPATH, value_to_search)
    search_program_button.click()
    print("Clicked 'חפש תוכניות לימוד אפשריות למסלול'")

    # Wait for the table to load
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))


def get_credits_and_prerequisites(driver,wait):
    """Extract course credits and prerequisite courses"""
    more_info_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//input[@type='button' and @value='פרטים נוספים' and contains(@class, 'btn-primary')]")
    ))
    more_info_button.click()

    # Extract credits
    credit_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@class='col' and contains(text(), 'נ\"ז')]")
    ))
    credits_pattern = r"נ\"ז : (\d+(\.\d+)?)"
    credit_type_match = re.search(credits_pattern, credit_element.text)
    credit_found = credit_type_match.group(1) if credit_type_match else '-1'

    # Extract prerequisite courses
    pre_course = set()
    pre_course_maybe = set()
    try:
        related_topics = driver.find_elements(By.XPATH,
                                              "//div[@class='col InRange'][label[contains(text(), 'נושא נקשר')]]")
        for topic in related_topics:
            print(topic.text)
            if topic.text.strip():
                pre_course.add(topic.text)

        related_topics = driver.find_elements(By.XPATH, "//div[@class='col InRange'][label[contains(text(), 'חליפי')]]")
        for topic in related_topics:
            print(topic.text)
            if topic.text.strip():
                pre_course_maybe.add(topic.text)
    except Exception:
        print("Didnt find Any PRE COURSES NEEDED YOU ARE THE BEST GILAD")

    time.sleep(1)
    return credit_found, pre_course, pre_course_maybe


def extract_course_info(driver, wait, course_subject, course_name, course_code, course_credit, pre_courses,
                        pre_courses_maybe):
    """Extract detailed information for a specific course"""
    #courses_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'Father')))
    group_and_type_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'TextAlignRight')))
    all_course_tables = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'Table.container.ncontainer.WithSearch')))
    courses = []
    for courseTable, group_and_type in zip(all_course_tables, group_and_type_section):
        try:
            html_text = group_and_type.get_attribute('innerHTML')
            courses_rows = courseTable.find_elements(By.CLASS_NAME, "row.Tr.Father")

            # Extract course type and group number
            course_type_pattern = r"(?<=קורס מסוג\s).*?(?=\s*&nbsp;)"
            group_pattern = r"קבוצה : (\d+)"

            course_type_match = re.search(course_type_pattern, html_text)
            course_type = course_type_match.group(0) if course_type_match else 'Didnt Find Course Type'

            group_match = re.search(group_pattern, html_text)
            group_number = group_match.group(1) if group_match else 'Didnt Find Group Number'

            print("Course Type:", course_type)
            print("Group Number:", group_number)
            for course in courses_rows:
                # Extract course details
                semester = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][1]").text.split(":")[
                    -1].strip()
                day = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][2]").text.split(":")[-1].strip()
                start_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][3]").text
                end_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][4]").text

                try:
                    lecturer = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][5]//a").text.strip()
                except Exception:
                    lecturer = "No Lecturer Yet"

                room = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][6]").text.split(":")[-1].strip()

                # Create course data dictionary
                course_data = {
                    "Course Subject": course_subject,
                    "Course Name": course_name,
                    "Course Code": course_code,
                    "Course Credit": course_credit,
                    "Course PreCondition": list(pre_courses),
                    "Course PreConditionAlt": list(pre_courses_maybe),
                    "Group Code": group_number,
                    "Lecture Type": course_type,
                    "Semester": semester,
                    "Day": day,
                    "StartTime": start_time,
                    "EndTime": end_time,
                    "Lecturer": lecturer,
                    "Room": room,
                }

                courses.append(course_data)

        except Exception as e:
            print(f"Error processing a course: {e}")

    return courses


def process_child_row(driver, wait, parent_row_index, child_row_index, course_subject):
    """Process a child row (specific course)"""
    flag = True
    courses_data = []

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

        # Check for popup
        try:
            popup_close_button = driver.find_element(By.XPATH,
                                                     "//button[@class='btn btn-secondary closefirstmodal' and @data-dismiss='modal']")
            popup_close_button.click()
            driver.back()
            print("Closed the popup modal")
            return [], True, child_row_index + 1
        except Exception:
            print("No popup detected")

        # Get prerequisites and credits
        if flag:
            course_credit, pre_courses, pre_courses_maybe = get_credits_and_prerequisites(driver, wait)
            flag = False
            driver.back()

        # Extract course information
        course_info = extract_course_info(
            driver, wait, course_subject, course_name, course_code,
            course_credit, pre_courses, pre_courses_maybe
        )
        courses_data.extend(course_info)

        # Navigate back
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
        driver.back()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
        time.sleep(8)

        return courses_data, True, child_row_index + 1

    except Exception as e:
        print(f"No more child rows to process or error. Last processed child row index: {child_row_index - 1}")
        print(f"Error: {e}")
        return courses_data, False, child_row_index


def process_parent_row(driver, wait, parent_row_index):
    """Process a parent row (course subject)"""
    all_courses_data = []

    try:
        parent_row_id = f"MyFather1000{parent_row_index}"
        parent_row_xpath = f"//div[@id='{parent_row_id}']"

        parent_row = driver.find_element(By.XPATH, parent_row_xpath)
        course_subject = parent_row.find_elements(By.XPATH, ".//div")[0].text
        if course_subject == 'קורסי חובה נוספים':
            return all_courses_data, True, parent_row_index + 1

        # Extract and navigate to the course link
        course_link = parent_row.find_elements(By.XPATH, ".//div")[1].find_element(By.TAG_NAME, "a").get_attribute(
            "href")
        print(f"Found course link: {course_link}")

        driver.get(course_link)
        print(f"Clicked the course link: {course_link}")

        # Wait for the page to load
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))

        # Process all child rows
        child_row_index = 1
        more_child_rows = True

        while more_child_rows:
            child_data, more_child_rows, child_row_index = process_child_row(
                driver, wait, parent_row_index, child_row_index, course_subject
            )
            all_courses_data.extend(child_data)

        # Navigate back to parent page
        driver.back()
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
        time.sleep(5)

        return all_courses_data, True, parent_row_index + 1

    except Exception as e:
        print(f"No more parent rows to process or error. Last processed parent row index: {parent_row_index - 1}")
        print(f"Error: {e}")
        return all_courses_data, False, parent_row_index


def save_to_json(courses_data, filename='courses_electricity.json'):
    """Save the collected data to a JSON file"""
    with open(filename, mode='w', encoding='utf-8') as file:
        json.dump(courses_data, file, ensure_ascii=False, indent=4)
    print(f"Data saved to {filename}")


def main():
    """Main function to run the course scraper"""
    # Initialize
    driver = setup_driver()
    wait = create_wait(driver)
    navigate_to_course_search(driver, wait,"הנדסת חשמל")

    # Initialize data collection
    all_courses_data = []
    parent_row_index = 6
    more_parent_rows = True

    # Process all parent rows (course subjects)
    while more_parent_rows:
        courses_data, more_parent_rows, parent_row_index = process_parent_row(driver, wait, parent_row_index)
        all_courses_data.extend(courses_data)

    # Save results and clean up
    save_to_json(all_courses_data)
    driver.quit()
    print("Scraping Ran Successfully")


if __name__ == "__main__":
    main()





# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import json
# import re
#
#
# def get_credits_and_pre(driver2):
#     more_info_button = driver2.find_element(By.XPATH,
#                                            "//input[@type='button' and @value='פרטים נוספים' and contains(@class, 'btn-primary')]")
#     more_info_button.click()
#     credit_element = driver2.find_element(By.XPATH, "//div[@class='col' and contains(text(), 'נ\"ז')]")
#     credits_patt = r"נ\"ז : (\d+(\.\d+)?)"
#
#     # Extract course type
#     credit_type_match = re.search(credits_patt, credit_element.text)
#     credit_found = credit_type_match.group(1) if credit_type_match else 'Didnt Find Credits'
#     pre_course = set()
#     pre_course_maybe = set()
#     try:
#         related_topics = driver.find_elements(By.XPATH, "//div[@class='col InRange'][label[contains(text(), 'נושא נקשר')]]")
#         for topic in related_topics:
#             print(topic.text)
#             if topic.text != ' ':
#                 pre_course.add(topic.text)
#         related_topics = driver.find_elements(By.XPATH, "//div[@class='col InRange'][label[contains(text(), 'חליפי')]]")
#         for topic in related_topics:
#             print(topic.text)
#             if topic.text != ' ':
#                 pre_course_maybe.add(topic.text)
#     except Exception:
#         print("Didnt find Any PRE COURSES NEEDED YOU ARE THE BEXT GILAD")
#     time.sleep(1)
#     return credit_found, pre_course, pre_course_maybe
#
#
# flag = True
# # Set up Selenium WebDriver
# driver = webdriver.Chrome()
#
# # Navigate to the starting page
# driver.get("https://yedionp.afeka.ac.il/yedion/fireflyweb.aspx?prgname=Enter_Search")
# with open('courses.json', mode='w', encoding='utf-8') as file:
#     courses_data = []
# # Wait for the selection element and click on "מדעי המחשב"
# wait = WebDriverWait(driver, 10)
#
#
# select_element = wait.until(EC.element_to_be_clickable((By.ID, "R1C9")))
#
# # Find the option for "מדעי המחשב" and click it
# option = select_element.find_element(By.XPATH, ".//option[@value='11']")
# option.click()
# print("Selected 'מדעי המחשב'")
#
# #time.sleep(2)
#
# show_courses_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='הצגת קורסים בתוכנית לימוד']")))
#
# show_courses_button.click()
# print("Clicked 'הצגת קורסים בתוכנית לימוד'")
#
# #time.sleep(2)
#
# valueToSearch = "//input[@value='חפש תוכניות לימוד אפשריות למסלול' and @class='btn btn-primary rounded g-mb-12']"
# # Wait for the page to load
# wait.until(EC.presence_of_element_located(
#     (By.XPATH, valueToSearch)))
#
# # Click on the button "חפש תוכניות לימוד אפשריות למסלול"
#
# search_program_button = driver.find_element(By.XPATH, valueToSearch)
# search_program_button.click()
# print("Clicked 'חפש תוכניות לימוד אפשריות למסלול'")
#
# # Wait for the page to load (adjust sleep time as necessary)
# #time.sleep(1)
#
# # Now we are at the page with the table containing program links
# table = wait.until(
#     EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#
# # Extract the links for courses (look for <a> elements with class 'btn btn-primary rounded g-mb-12')
# links = driver.find_elements(By.XPATH, "//a[@class='btn btn-primary rounded g-mb-12']")
#
# parent_row_index = 1
# while True:
#     parent_row_id = f"MyFather1000{parent_row_index}"
#     parent_row_xpath = f"//div[@id='{parent_row_id}']"
#     if parent_row_index == 6: # לומדה can be more abstract
#         parent_row_index += 1
#         continue
#     try:
#         parent_row = driver.find_element(By.XPATH, parent_row_xpath)
#         course_subject = parent_row.find_elements(By.XPATH, ".//div")[0].text
#         # Extract the course link
#         course_link = parent_row.find_elements(By.XPATH, ".//div")[1].find_element(By.TAG_NAME, "a").get_attribute("href")
#         print(f"Found course link: {course_link}")
#
#         # Click the course link
#         driver.get(course_link)
#         print(f"Clicked the course link: {course_link}")
#
#         # Wait for the page to load
#         wait.until(EC.presence_of_element_located(
#             (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#
#         child_row_index = 1
#         while True:
#             try:
#                 child_row_id = f"MyFather1000{child_row_index}"
#                 child_row_xpath = f"//div[@id='{child_row_id}']"
#
#                 child_row = driver.find_element(By.XPATH, child_row_xpath)
#                 course_name = child_row.find_elements(By.XPATH, ".//div")[1].text
#                 course_code = child_row.find_elements(By.XPATH, ".//div")[0].text
#
#                 # Find and click the button
#                 button = child_row.find_element(By.XPATH,
#                                                 ".//input[@value='חיפוש קורס במערכת השעות' and @tabindex='0']")
#                 button.click()
#                 print(f"Clicked button in row {child_row_id} for course: {course_name}")
#                 try:
#                     popup_close_button = driver.find_element(By.XPATH,
#                                                              "//button[@class='btn btn-secondary closefirstmodal' and @data-dismiss='modal']")
#                     popup_close_button.click()
#                     driver.back()
#                     child_row_index += 1
#                     time.sleep(2)
#                     print("Closed the popup modal")
#                     continue
#                 except Exception:
#                     print("No popup detected")
#                 ## GET Pre Requesite And Credits Points
#                 if flag:
#                     course_credit, pre_courses, pre_courses_maybe = get_credits_and_pre(driver)
#                     #time.sleep(4)
#                     flag = False
#                     driver.back()
#                 courses_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'Father')))
#                 GroupAndType_section = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'TextAlignRight')))
#
#                 courses = []
#                 for course, groupAndType in zip(courses_section, GroupAndType_section):
#                     try:
#                         htmlText = groupAndType.get_attribute('innerHTML')
#                         # Regular expression patterns
#                         course_type_pattern = r"(?<=קורס מסוג\s).*?(?=\s*&nbsp;)"
#                         group_pattern = r"קבוצה : (\d+)"
#
#                         # Extract course type
#                         course_type_match = re.search(course_type_pattern, htmlText)
#                         course_type = course_type_match.group(0) if course_type_match else 'Didnt Find Course Type'
#                         # Extract group number
#                         group_match = re.search(group_pattern, htmlText)
#                         group_number = group_match.group(1) if group_match else 'Didnt Find Group Number'
#                         print("Course Type:", course_type)
#                         print("Group Number:", group_number)
#                         semester = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][1]").text.split(":")[-1].strip()
#                         day = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][2]").text.split(":")[
#                             -1].strip()
#                         start_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][3]").text
#                         end_time = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][4]").text
#                         try:
#                             lecturer = course.find_element(By.XPATH,
#                                                            ".//div[contains(@class, 'InRange')][5]//a").text.strip()
#                         except Exception:
#                             lecturer = "No Lecturer Yet"  # If the lecturer is not found, assign an empty string
#                         room = course.find_element(By.XPATH, ".//div[contains(@class, 'InRange')][6]").text.split(":")[
#                             -1].strip()
#
#                         courses.append({
#                             "Course Subject": course_subject,
#                             "Course Name": course_name,
#                             "Course Code": course_code,
#                             "Course Credit": course_credit,
#                             "Course PreCondition": list(pre_courses),
#                             "Course PreConditonMaybe": list(pre_courses_maybe),
#                             "Group Code": group_number,
#                             "Lecture Type": course_type,
#                             "Semester": semester,
#                             "Day": day,
#                             "StartTime": start_time,
#                             "EndTime": end_time,
#                             "Lecturer": lecturer,
#                             "Room": room,
#                         })
#                     except Exception as e:
#                         print(f"Error processing a course: {e}")
#
#                 courses_data.extend(courses)
#
#                 # Wait for the new page to load
#                 wait.until(EC.presence_of_element_located(
#                     (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#
#                 driver.back()
#                 wait.until(EC.presence_of_element_located(
#                     (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#                 time.sleep(2)
#
#                 child_row_index += 1
#                 flag = True
#
#             except Exception as e:
#                 print(f"No more child rows to process. Last processed child row index: {child_row_index - 1}")
#                 break
#
#         driver.back()
#         wait.until(EC.presence_of_element_located(
#             (By.XPATH, "//div[contains(@class, 'Table container ncontainer WithSearch')]")))
#         time.sleep(5)
#
#         parent_row_index += 1
#
#     except Exception as e:
#         print(f"No more parent rows to process. Last processed parent row index: {parent_row_index - 1}")
#         break
#
# # Write all extracted courses data to the JSON file
# with open('courses.json', mode='w', encoding='utf-8') as file:
#     json.dump(courses_data, file, ensure_ascii=False, indent=4)
#
# # Close the browser
# driver.quit()
#
#
#
