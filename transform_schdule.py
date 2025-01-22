import json


def transform_schedule(input_file, output_file):
    # Open and read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    transformed_data = []
    courses_dict = {}

    # Iterate through the data to group by course code
    for entry in data:
        course_code = entry["Course Code"]

        # If course code is not yet in courses_dict, initialize it
        if course_code not in courses_dict:
            courses_dict[course_code] = {
                "Course_Type": entry["Course Subject"],
                "Course_Name": entry["Course Name"],
                "Course_Code": entry["Course Code"],
                "Semester": entry["Semester"],
                "Department": "cs",
                "Prerequisites": [],
                "Groups": []  # Initialize groups as an empty list
            }

        # Create a group entry for the given course and add it to the "Groups" field
        group_entry = {
            "GroupsCode": entry['Group Code'],
            "lectureType": getLectureType(entry['Lecture Type']),
            "startTime": entry["StartTime"].strip(),
            "endTime": entry["EndTime"].strip(),
            "room": entry["Room"],
            "lecturer": entry["Lecturer"],
            "dayOfWeek": getDayByName(entry["Day"]),
        }

        # Add this group entry to the correct course entry in the dictionary
        courses_dict[course_code]["Groups"].append(group_entry)

    # Convert the dictionary values to a list and write to output file
    transformed_data = list(courses_dict.values())

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


def getLectureType(name):
    lecturetype = {
        "סופי-הרצאה+תרגול": 0,
        "מעבדה": 2,
        "תרגול": 1,
        'סופי-הרצאה+מעבדה': 3
    }
    return lecturetype.get(name, "Invalid day name")


if __name__ == "__main__":
    input_file = 'd:/Projects/PycharmProjects/CourseExtractAfeka/courses.json'
    output_file = 'd:/Projects/PycharmProjects/CourseExtractAfeka/coursesWorked_transformed.json'
    transform_schedule(input_file, output_file)