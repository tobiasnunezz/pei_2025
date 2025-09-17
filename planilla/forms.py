from django import forms
from django.contrib.auth.models import User
from .models import Tablero, PerfilUsuario

CUALITATIVOS = [
    ("no iniciado", "No Iniciado"),
    ("en proceso", "En proceso"),
    ("presentado", "Presentado"),
    ("aprobado", "Aprobado"),
]

def obtener_campo_avance_por_tipo(tipo_meta):
    if tipo_meta == "porcentaje":
        return forms.FloatField(
            label="Avance (%)",
            required=True,
            min_value=0,
            max_value=100,
            widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            help_text='Ingresar el valor en porcentaje (ej: 42.5)'
        )
    elif tipo_meta == "texto":
        return forms.ChoiceField(
            choices=CUALITATIVOS,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=True,
            label="Avance"
        )
    else:
        return forms.CharField(
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=True,
            label="Avance"
        )

class AvanceForm(forms.ModelForm):
    observacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label="Observación"
    )
    evidencias = forms.FileField(
        required=False,
        label="Adjuntar evidencias (PDF, Word, Excel, Imágenes)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'multiple': ''})
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
        tipo_meta = self.instance.tipo_meta
        self.fields['avance'] = obtener_campo_avance_por_tipo(tipo_meta)

    def clean(self):
        cleaned_data = super().clean()
        tablero = self.instance
        tablero.avance = cleaned_data.get('avance')
        tablero.calcular_nivel_y_accion()
        cleaned_data['nivel'] = tablero.nivel
        cleaned_data['accion'] = tablero.accion
        return cleaned_data

class TableroCompletoForm(forms.ModelForm):
    observacion = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label="Observación"
    )

    class Meta:
        model = Tablero
        fields = '__all__'
        widgets = {
            'eje_estrategico': forms.TextInput(attrs={'class': 'form-control'}),
            'objetivo_estrategico': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'indicador': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meta_2025': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_meta': forms.Select(attrs={'class': 'form-select'}),
            'nivel': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'accion': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tipo_meta = self.instance.tipo_meta
        self.fields['avance'] = obtener_campo_avance_por_tipo(tipo_meta)

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
