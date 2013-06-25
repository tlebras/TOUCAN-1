from django import forms
 
class UploadForm(forms.Form):
    data = forms.FileField()
