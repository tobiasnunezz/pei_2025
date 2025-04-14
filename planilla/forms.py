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

AVANCE_CHOICES = CUANTITATIVOS + CUALITATIVOS

# ✏️ Formulario para usuarios comunes
class AvanceForm(forms.ModelForm):
    avance = forms.ChoiceField(
        choices=AVANCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = Tablero
        fields = ['avance']

    def clean(self):
        cleaned_data = super().clean()
        avance = cleaned_data.get('avance')

        # Asignación automática de nivel y acción
        if avance is not None:
            tablero = self.instance

            if avance == "0":
                tablero.nivel = "No existe avance"
                tablero.accion = "Correctiva"
            elif avance == "1":
                tablero.nivel = "Bajo"
                tablero.accion = "Correctiva"
            elif avance == "25":
                tablero.nivel = "Aceptable"
                tablero.accion = "Preventiva"
            elif avance == "50":
                tablero.nivel = "Medio"
                tablero.accion = "Preventiva"
            elif avance == "75":
                tablero.nivel = "Satisfactorio"
                tablero.accion = "Analizar tendencias"
            elif avance == "90":
                tablero.nivel = "Óptimo"
                tablero.accion = "Analizar tendencias"
            elif avance == "No Iniciado":
                tablero.nivel = "No existe avance"
                tablero.accion = "Correctiva"
            elif avance == "En proceso":
                tablero.nivel = "Medio"
                tablero.accion = "Preventiva"
            elif avance in ["Aprobado", "Presentado", "Aprobado/Presentado-a"]:
                tablero.nivel = "Óptimo"
                tablero.accion = "Analizar tendencias"

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


class TableroCompletoForm(forms.ModelForm):
    class Meta:
        model = Tablero
        fields = '__all__'
        widgets = {
            'eje_estrategico': forms.TextInput(attrs={'class': 'form-control'}),
            'objetivo_estrategico': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'indicador': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_2025': forms.TextInput(attrs={'class': 'form-control'}),
            'avance': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel': forms.TextInput(attrs={'class': 'form-control'}),
            'accion': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
        }
