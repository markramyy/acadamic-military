from django import forms
from faculties.models import Faculty
from assignments.models import Student


class BulkStudentCreationForm(forms.Form):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        label="الكلية",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    count = forms.IntegerField(
        min_value=1, max_value=1000,
        label="عدد الطلاب",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    start_number = forms.IntegerField(
        min_value=1, required=False,
        label="رقم البداية",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=Student.GENDER_CHOICES,
        label="الجنس",
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='M'
    )

    def clean_count(self):
        count = self.cleaned_data.get('count')
        if count > 1000:
            raise forms.ValidationError("لا يمكن إنشاء أكثر من 1000 طالب في العملية الواحدة")
        return count


class StudentFilterForm(forms.Form):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        label="الكلية",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    gender = forms.ChoiceField(
        choices=(('', 'الكل'),) + Student.GENDER_CHOICES,
        label="الجنس",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
