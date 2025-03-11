from django.db import models

from core.models import BaseModel
from faculties.models import Faculty
from researches.models import Research


class Student(BaseModel):
    """Student model"""
    GENDER_CHOICES = (
        ('M', 'ذكر'),
        ('F', 'أنثى'),
    )

    name = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=20)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='students')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

    class Meta:
        unique_together = ('serial_number', 'faculty')


class Assignment(BaseModel):
    """Research assignment model"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignments')
    research = models.ForeignKey(Research, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateField(auto_now_add=True)
    group_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.student} - {self.research}"

    @property
    def group_research_key(self):
        """
        A unique key for grouping assignments by research and group.
        This is used for the template's regroup tag.
        """
        # If group_id exists, use research_id+group_id+faculty_id as the key
        faculty_id = self.student.faculty_id
        if self.group_id:
            return f"{self.research_id}_{self.group_id}_{faculty_id}"
        # Otherwise, use a combination that includes the faculty
        return f"{self.research_id}_ind_{faculty_id}_{self.id}"
