from django import forms
from django.contrib.auth.models import User
from .models import Tablero, PerfilUsuario

CUANTITATIVOS = [
    ("", "---------"),
    ("0", "0%"),
    ("1", "1 – 24%"),
    ("25", "25 – 49%"),
    ("50", "50 – 74%"),
    ("75", "75 – 89%"),
    ("90", ">= 90%"),
]

CUALITATIVOS = [
    ("No Iniciado", "No Iniciado"),
    ("En proceso", "En proceso"),
    ("Presentado", "Aprobado/Presentado-a"),
]

class AvanceForm(forms.ModelForm):
    observacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label="Observación"
    )

    class Meta:
        model = Tablero
        fields = ['avance', 'observacion', 'nivel', 'accion']
        widgets = {
            'nivel': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'accion': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tablero = self.instance
        tipo = getattr(tablero, 'tipo_meta', 'porcentaje')

        if tipo == "porcentaje":
            self.fields['avance'] = forms.ChoiceField(
                choices=CUANTITATIVOS,
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=True,
                help_text="Seleccione el rango de cumplimiento en porcentaje."
            )
        elif tipo == "texto":
            self.fields['avance'] = forms.ChoiceField(
                choices=CUALITATIVOS,
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=True,
                help_text="Seleccione el estado de avance correspondiente."
            )
        else:  # tipo == "numero"
            self.fields['avance'] = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                required=True,
                label="Avance",
                help_text="Ingrese un número según la meta definida."
            )

    def clean(self):
        cleaned_data = super().clean()
        tablero = self.instance

        tablero.avance = cleaned_data.get('avance')
        tablero.calcular_nivel_y_accion()

        cleaned_data['nivel'] = tablero.nivel
        cleaned_data['accion'] = tablero.accion
        return cleaned_data

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['user', 'responsable']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CrearUsuarioForm(forms.ModelForm):
    responsable = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            PerfilUsuario.objects.create(
                user=user,
                responsable=self.cleaned_data['responsable']
            )
        return user
