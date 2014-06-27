from django import forms

class CadenceWidget(forms.widgets.MultiWidget):
	def __init__(self, *args, **kwargs):
		choices = kwargs.pop("choices", [
			(1,  "second(s)"),
			(60, "minute(s)"),
			(3600, "hour(s)"),
			(86400, "day(s)")
		])
		
		widgets = [forms.NumberInput(), forms.Select(choices=choices)]
		
		super(CadenceWidget, self).__init__(widgets, *args, **kwargs)
 
	def decompress(self, value):
		return [value, 1]

class CadenceField(forms.fields.MultiValueField):
	
	def __init__(self, *args, **kwargs):
		choices = kwargs.pop("choices", [
			(1,  "second(s)"),
			(60, "minute(s)"),
			(3600, "hour(s)"),
			(86400, "day(s)")
		])
		required = kwargs.get("required", True)
		min_value = kwargs.pop("min_value", 1)
		fields = [forms.IntegerField(required = required, min_value = min_value), forms.TypedChoiceField(required = required, coerce=int, choices=choices)]
		
		super(CadenceField, self).__init__(fields=fields, *args, **kwargs)
		
		self.widget = CadenceWidget(choices = choices)
	
	def compress(self, values):
		if values:
			try:
				result = int(values[0])
			except Exception:
				return values[0]
			else:
				if values[1]:
					return result * values[1]
					
				else:
					return result
		else:
			return None

if __name__ == "__main__":
	class TestForm(forms.Form):
		cadence = CadenceField(required=False, help_text = "Cadence test")
	
	test_form = TestForm({"cadence_0": 10, "cadence_1": 3600})
	test_form.is_valid()
	test_form.errors
	test_form.cleaned_data

