from django import template
from collections import defaultdict
from assignments.models import Assignment
from django.db.models import Count

register = template.Library()


@register.filter
def group_assignments_by_research(assignments):
    """
    Group assignments by research and group ID
    """
    grouped = defaultdict(list)

    for assignment in assignments:
        key = f"{assignment.research_id}_{assignment.group_id or assignment.id}"
        grouped[key].append(assignment)

    return grouped.values()


# Keep the existing filters
@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using the key
    """
    if dictionary and key in dictionary:
        return dictionary[key]
    return None


@register.filter
def get_research_assignment_count(faculties, research_id):
    count = 0
    for faculty in faculties:
        if research_id in faculty['assignments_by_research']:
            count += faculty['assignments_by_research'][research_id]['count']
    return count


@register.filter
def divide(value, arg):
    try:
        return value / arg
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def multiply(value, arg):
    try:
        return value * arg
    except ValueError:
        return 0


@register.filter
def get_research_group_count(faculties, research_id):
    # Count the number of unique group IDs for this research
    groups = Assignment.objects.filter(research_id=research_id).values('group_id').annotate(count=Count('group_id'))
    return groups.count()
