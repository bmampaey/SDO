from django import forms
from django.core import validators
from django.core.exceptions import ValidationError

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




# Source https://gist.github.com/eerien/7002396

class MinLengthValidator(validators.MinLengthValidator):
	message = 'Ensure this value has at least %(limit_value)d elements (it has %(show_value)d).'

class MaxLengthValidator(validators.MaxLengthValidator):
	message = 'Ensure this value has at most %(limit_value)d elements (it has %(show_value)d).'


class CommaSeparatedCharField(forms.Field):
	def __init__(self, dedup=True, max_length=None, min_length=None, *args, **kwargs):
		self.dedup, self.max_length, self.min_length = dedup, max_length, min_length
		super(CommaSeparatedCharField, self).__init__(*args, **kwargs)
		if min_length is not None:
			self.validators.append(MinLengthValidator(min_length))
		if max_length is not None:
			self.validators.append(MaxLengthValidator(max_length))

	def to_python(self, value):
		if value in validators.EMPTY_VALUES:
			return []

		value = [item.strip() for item in value.split(',') if item.strip()]
		if self.dedup:
			value = list(set(value))

		return value

	def clean(self, value):
		value = self.to_python(value)
		self.validate(value)
		self.run_validators(value)
		return value


class CommaSeparatedIntegerField(forms.Field):
	default_error_messages = {
		'invalid': 'Enter comma separated numbers only.',
	}

	def __init__(self, dedup=True, max_length=None, min_length=None, *args, **kwargs):
		self.dedup, self.max_length, self.min_length = dedup, max_length, min_length
		super(CommaSeparatedIntegerField, self).__init__(*args, **kwargs)
		if min_length is not None:
			self.validators.append(MinLengthValidator(min_length))
		if max_length is not None:
			self.validators.append(MaxLengthValidator(max_length))

	def to_python(self, value):
		if value in validators.EMPTY_VALUES:
			return []

		try:
			value = [int(item.strip()) for item in value.split(',') if item.strip()]
			if self.dedup:
				value = list(set(value))
		except (ValueError, TypeError):
			raise ValidationError(self.error_messages['invalid'])

		return value

	def clean(self, value):
		value = self.to_python(value)
		self.validate(value)
		self.run_validators(value)
		return value

if __name__ == "__main__":
	class TestForm(forms.Form):
		cadence = CadenceField(required=False, help_text = "Cadence test")
	
	test_form = TestForm({"cadence_0": 10, "cadence_1": 3600})
	test_form.is_valid()
	test_form.errors
	test_form.cleaned_data

