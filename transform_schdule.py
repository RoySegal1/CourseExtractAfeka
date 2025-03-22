import json


def transform_schedule(input_file, output_file):
    # Open and read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    transformed_data = []
    courses_dict = {}

    # Iterate through the data to group by course code and semester
    for entry in data:
        course_code = entry["Course Code"]
        semester = entry["Semester"]

        # Unique key combining course code and semester
        course_key = f"{course_code}_{semester}"

        # If course key is not yet in courses_dict, initialize it
        if course_key not in courses_dict:
            courses_dict[course_key] = {
                "courseType": clean_course_subject(entry["Course Subject"]),
                "courseName": entry["Course Name"],
                "courseCode": entry["Course Code"] + "-" +getLastSuffixforCode(entry["Semester"]),
                "semester": entry["Semester"],
                "department": "cs",
                "prerequisites": [],
                "groups": []  # Initialize groups as an empty list
            }

        # Create a group entry for the given course and add it to the "Groups" field
        group_entry = {
            "groupCode": entry['Group Code'] + '/1' if getLectureType(entry['Lecture Type']) == 1 else entry['Group Code'],
            "lectureType": getLectureType(entry['Lecture Type']),
            "startTime": entry["StartTime"].strip(),
            "endTime": entry["EndTime"].strip(),
            "room": entry["Room"],
            "lecturer": entry["Lecturer"],
            "dayOfWeek": getDayByName(entry["Day"])
        }

        # Add this group entry to the correct course entry in the dictionary
        courses_dict[course_key]["groups"].append(group_entry)

    # Convert the dictionary values to a list and write to output file
    transformed_data = list(courses_dict.values())
    # Sort the data by courseType
    transformed_data = sorted(transformed_data, key=lambda x: x["courseType"])

    # Write the transformed data to the output JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=4)

def getDayByName(name):
    days = {
        "א": 0,
        "ב": 1,
        "ג": 2,
        "ד": 3,
        "ה": 4,
        "ו": 5,
        "ש": 6
    }
    return days.get(name, "Invalid day name")
def getLastSuffixforCode(semester):
    semesters = {
        "א": "1",
        "ב": "2",
        "קיץ": "3"
    }
    return semesters.get(semester, "Invalid day name")


def clean_course_subject(subject):
    # This will replace spaces with '' and remove any unwanted apostrophes.
    return subject.replace("'", "")


def getLectureType(name):
    lecturetype = {
        "סופי-הרצאה+תרגול": 0,
        "מעבדה": 1,
        "תרגול": 1,
        'סופי-הרצאה+מעבדה': 0
    }
    return lecturetype.get(name, "Invalid day name")


if __name__ == "__main__":
    input_file = './courses.json'
    output_file = './coursesWorked_transformed4.json'
    transform_schedule(input_file, output_file)