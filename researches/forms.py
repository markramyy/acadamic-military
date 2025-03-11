from django import forms
from researches.models import Research


class ResearchForm(forms.ModelForm):
    class Meta:
        model = Research
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم البحث',
                'dir': 'rtl'
            })
        }
        labels = {
            'name': 'اسم البحث',
        }
        error_messages = {
            'name': {
                'unique': 'هذا البحث موجود بالفعل',
                'required': 'يجب إدخال اسم البحث',
            }
        }
