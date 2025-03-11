import random
import uuid
from django.db import transaction
from collections import defaultdict


@transaction.atomic
def randomly_assign_researches(students, researches, group_size=1):
    """
    Randomly assign researches to students with specified group size,
    ensuring groups are formed only from students of the same faculty and gender.

    Args:
        students: QuerySet of Student objects
        researches: QuerySet of Research objects
        group_size: Number of students per research group (1-100)

    Returns:
        tuple: (success_count, error_count)
    """
    from assignments.models import Assignment

    if not students or not researches:
        return 0, 0

    # Convert QuerySets to lists for shuffling
    student_list = list(students)
    research_list = list(researches)

    # Shuffle the research list for randomization
    random.shuffle(research_list)

    success_count = 0
    error_count = 0

    # Group students by faculty and gender
    students_by_faculty_gender = defaultdict(list)
    for student in student_list:
        key = f"{student.faculty_id}_{student.gender}"
        students_by_faculty_gender[key].append(student)

    # Shuffle students within each group
    for key in students_by_faculty_gender:
        random.shuffle(students_by_faculty_gender[key])

    # We'll use this to track which research is assigned to which group
    research_group_counts = {research.id: 0 for research in research_list}

    # Process each faculty-gender combination separately
    for faculty_gender_key, students_in_group in students_by_faculty_gender.items():
        # Organize students into groups within the same faculty and gender
        student_groups = []

        if group_size > 1:
            # Divide students into groups within the same faculty and gender
            for i in range(0, len(students_in_group), group_size):
                group = students_in_group[i:i + group_size]
                if len(group) == group_size:  # Only use complete groups
                    student_groups.append(group)
                else:
                    # Handle leftover students individually
                    for student in group:
                        student_groups.append([student])
        else:
            # Each student is a group of 1
            student_groups = [[student] for student in students_in_group]

        # Assign researches to groups within this faculty-gender combination
        for group in student_groups:
            # Pick a research for this group
            if not research_list:
                error_count += len(group)
                continue

            # If all researches have been used once, reset the list
            if not any(research_group_counts[research.id] == 0 for research in research_list):
                for research_id in research_group_counts:
                    research_group_counts[research_id] = 0

            # Try to find a research that hasn't been used yet
            available_researches = [r for r in research_list if research_group_counts[r.id] == 0]

            if available_researches:
                research = random.choice(available_researches)
            else:
                research = random.choice(research_list)

            # Generate a unique group ID if there's more than one student in the group
            group_id = str(uuid.uuid4())[:8] if len(group) > 1 else None

            # Assign the same research to all students in the group
            for student in group:
                try:
                    Assignment.objects.create(
                        student=student,
                        research=research,
                        group_id=group_id
                    )
                    success_count += 1
                    research_group_counts[research.id] += 1
                except Exception:
                    error_count += 1

    return success_count, error_count
