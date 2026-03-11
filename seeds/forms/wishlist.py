from django import forms

from .models import SeedWishlist


class SeedWishlistForm(forms.ModelForm):
    class Meta:
        model = SeedWishlist
        exclude = ("user", "created_at", "updated_at", "acquired_seed")
        widgets = {
            "follow_up_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            field.widget.attrs["class"] = css_class
