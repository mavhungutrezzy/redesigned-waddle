from django import forms


class QuickBatchSearchForm(forms.Form):
    batch_number = forms.CharField(
        max_length=255,
        label="Batch number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. V-202512-0001",
                "autocomplete": "off",
            }
        ),
    )


class QuickQRSearchForm(forms.Form):
    qr_content = forms.CharField(
        label="QR content",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Scan QR code or paste its content here",
                "autocomplete": "off",
            }
        ),
    )
