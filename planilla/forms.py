from django import forms
from django.contrib.auth.models import User
from .models import Tablero, PerfilUsuario

# Opciones de avance
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

    def clean(self):
        cleaned_data = super().clean()
        tablero = self.instance

        # Cargar los valores del form para cálculo
        tablero.avance = cleaned_data.get('avance')
        tablero.calcular_nivel_y_accion()

        # Cargar al formulario lo calculado (visualmente)
        cleaned_data['nivel'] = tablero.nivel
        cleaned_data['accion'] = tablero.accion
        return cleaned_data

# 🧑‍💼 Formulario para el admin con todos los campos
class TableroCompletoForm(forms.ModelForm):
    avance = forms.ChoiceField(
        choices=AVANCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = Tablero
        fields = '__all__'
        widgets = {
            'eje_estrategico': forms.TextInput(attrs={'class': 'form-control'}),
            'objetivo_estrategico': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'indicador': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_2025': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel': forms.TextInput(attrs={'class': 'form-control'}),
            'accion': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# 👤 Formulario para modificar responsable del perfil de usuario
class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['user', 'responsable']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
        }

# 🆕 Crear nuevo usuario + perfil (staff)
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
