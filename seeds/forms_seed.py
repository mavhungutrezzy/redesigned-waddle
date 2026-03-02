from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Seed, SeedPhoto


class SeedForm(forms.ModelForm):
    class Meta:
        model = Seed
        exclude = ("user", "batch_number", "created_at", "updated_at", "qr_code")
        widgets = {
            "date_collected": forms.DateInput(attrs={"type": "date"}),
            "best_before": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = (
                "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )
            field.widget.attrs["class"] = css_class

    def clean(self):
        cleaned_data = super().clean()
        date_collected = cleaned_data.get("date_collected")
        best_before = cleaned_data.get("best_before")
        if date_collected and best_before and best_before < date_collected:
            self.add_error(
                "best_before",
                "Best before date must be on or after collected date.",
            )
        return cleaned_data


class SeedPhotoForm(forms.ModelForm):
    class Meta:
        model = SeedPhoto
        fields = ("image",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].widget.attrs.update(
            {
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp,image/gif",
            }
        )
        if "DELETE" in self.fields:
            self.fields["DELETE"].widget.attrs["class"] = "form-check-input"


class BaseSeedPhotoFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = 0
        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
                continue
            if form.cleaned_data.get("image"):
                total += 1
            elif form.instance.pk:
                total += 1
        if total > 3:
            raise forms.ValidationError("You can upload at most 3 photos per seed.")


SeedPhotoFormSet = inlineformset_factory(
    Seed,
    SeedPhoto,
    form=SeedPhotoForm,
    formset=BaseSeedPhotoFormSet,
    extra=3,
    can_delete=True,
    max_num=3,
    validate_max=True,
)
