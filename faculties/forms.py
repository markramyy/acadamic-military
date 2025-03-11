from django import forms
from faculties.models import Faculty


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم الكلية',
                'dir': 'rtl'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل رمز الكلية (مثل: CS, MED, ENG)',
                'dir': 'ltr'
            })
        }
        labels = {
            'name': 'اسم الكلية',
            'code': 'رمز الكلية',
        }
        error_messages = {
            'name': {
                'required': 'يجب إدخال اسم الكلية',
            },
            'code': {
                'unique': 'هذا الرمز موجود بالفعل',
                'required': 'يجب إدخال رمز الكلية',
                'max_length': 'يجب ألا يتجاوز رمز الكلية 10 أحرف',
            }
        }
