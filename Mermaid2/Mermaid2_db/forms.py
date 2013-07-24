from django import forms
from Mermaid2_db.models import Deployment, Point, Instrument, Measurement, InstrumentWavelength

             
def choices():
    """Fonction making the list of available instruments
    """

    list_instruments = [] #create empty list

    for instrument in Instrument.objects.all(): #get all instrument objects
        list_instruments.append([instrument.id, instrument.name]) #add the object to the list

    return list_instruments
	
	
class UploadForm(forms.Form):
    """Form for uploading files
    """
        
    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        self.fields['data'] = forms.FileField()        
        self.fields['name'] = forms.ChoiceField(choices=choices())
	
	
class AddInstrumentForm(forms.Form):
    
    name = forms.CharField(max_length=100)
    wavelengths = forms.IntegerField()
    
    def clean_name(self):
        name = self.cleaned_data.get('name')    
        if Instrument.objects.filter(name=name).exists():
            instrument = Instrument.objects.filter(name=name)
            wavelengths = InstrumentWavelength.objects.filter(instrument=instrument)
            wave_list = []
            for wave in wavelengths:
                wave_list.append(wave.value)
            print wave_list
            raise forms.ValidationError('This instrument already exists. Wavelengths : {}'.format(wave_list))
   
        return name   
    
    
class AddWavelengthForm(forms.Form):

    def __init__(self, *args, **kwargs):
        num_wav = kwargs.pop('num_wav')
        super(AddWavelengthForm, self).__init__(*args, **kwargs)
        for wave in range(num_wav):
            self.fields['wavelength %d' % (wave+1)] = forms.FloatField()
            
            
class SearchMeasurementForm(forms.Form):

    def __init__(self, *args, **kwargs):
        
        deployment_choices = kwargs.pop('deployment_choices')
        measurement_type_choices = kwargs.pop('measurement_type_choices')
        wavelengths_choices = kwargs.pop('wavelengths_choices')
        super(SearchMeasurementForm, self).__init__(*args, **kwargs)
        self.fields['deployment'] = forms.MultipleChoiceField(required=False, choices=deployment_choices)
        self.fields['measurement_type'] = forms.MultipleChoiceField(required=False, choices=measurement_type_choices)
        self.fields['wavelengths'] = forms.MultipleChoiceField(required=False, choices=wavelengths_choices)   
    
    
class SearchPointForm(forms.Form):

    top_left_lat = forms.FloatField()
    top_left_lon = forms.FloatField()
    bot_right_lat = forms.FloatField()
    bot_right_lon = forms.FloatField()    









