from django import forms
from django.core.validators import RegexValidator
from PIL import Image
from .models import Usuario, Producto
import re


class UsuarioRegistroForm(forms.ModelForm):
    confirmar_contraseña = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su contraseña'
        })
    )

    class Meta:
        model = Usuario
        fields = [
            "rut",
            "nombre",
            "apellidoPaterno",
            "apellidoMaterno",
            "contraseña",
            "rol",
        ]
        widgets = {
            "contraseña": forms.PasswordInput(attrs={
                'class': 'form-control password-validation',
                'data-requirements': 'true',
                'placeholder': 'Ingrese su contraseña'
            }),
        }
        error_messages = {
            'rut': {
                'unique': 'Ya existe un usuario registrado con este RUT.'
            }
        }

    def clean_contraseña(self):
        contraseña = self.cleaned_data.get('contraseña')
        
        # Validaciones de contraseña
        if not any(char.islower() for char in contraseña):
            raise forms.ValidationError('La contraseña debe contener al menos una letra minúscula.')
            
        if not any(char.isupper() for char in contraseña):
            raise forms.ValidationError('La contraseña debe contener al menos una letra mayúscula.')
            
        if not any(char.isdigit() for char in contraseña):
            raise forms.ValidationError('La contraseña debe contener al menos un número.')
            
        if len(contraseña) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
            
        return contraseña

    def clean(self):
        cleaned_data = super().clean()
        contraseña = cleaned_data.get("contraseña")
        confirmar = cleaned_data.get("confirmar_contraseña")

        if contraseña and confirmar:
            if contraseña != confirmar:
                raise forms.ValidationError("Las contraseñas no coinciden")

            # Validaciones adicionales de contraseña
            if len(contraseña) < 8:
                raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres")
            
            if not re.search("[a-z]", contraseña):
                raise forms.ValidationError("La contraseña debe contener al menos una letra minúscula")
            
            if not re.search("[A-Z]", contraseña):
                raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula")
            
            if not re.search("[0-9]", contraseña):
                raise forms.ValidationError("La contraseña debe contener al menos un número")

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de ayuda
        self.fields['contraseña'].help_text = None
        self.fields['confirmar_contraseña'].help_text = None
        
        # Agregar clases y atributos para validación en tiempo real
        self.fields['contraseña'].widget.attrs.update({
            'class': 'form-control password-validation',
            'data-requirements': 'true'
        })

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        
        # Eliminar puntos y convertir a mayúsculas
        rut = rut.replace(".", "").replace(" ", "").upper()
        
        # Verificar formato básico (XXXXXXXX-X)
        if not re.match(r'^\d{7,8}-[\dK]$', rut):
            raise forms.ValidationError("El formato del RUT debe ser XXXXXXXX-X (sin puntos)")
        
        rut_sin_dv = rut[:-2]  # Obtener números antes del guión
        dv = rut[-1]  # Obtener dígito verificador
        
        try:
            rut_num = int(rut_sin_dv)
        except ValueError:
            raise forms.ValidationError("El RUT debe contener solo números antes del guión")
        
        # Algoritmo para calcular dígito verificador
        multiplicador = 2
        suma = 0
        
        # Calcular suma
        for d in reversed(str(rut_num)):
            suma += int(d) * multiplicador
            multiplicador = multiplicador + 1 if multiplicador < 7 else 2
        
        # Calcular dígito verificador
        resto = suma % 11
        dv_calculado = str(11 - resto) if resto > 1 else str(0 if resto == 0 else 'K')
        
        # Comparar con el dígito verificador ingresado
        if dv != dv_calculado:
            raise forms.ValidationError(f"El RUT ingresado no es válido. DV correcto: {dv_calculado}")
        
        return rut


class LoginForm(forms.Form):
    rut = forms.CharField(
        label="RUT",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Ingrese su RUT"}
        ),
    )
    contraseña = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Ingrese su contraseña"}
        ),
    )


class ProductoForm(forms.ModelForm):
    # Validador para el nombre (solo letras, números y espacios)
    nombre_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9\s]+$",
        message="El nombre solo puede contener letras, números y espacios",
    )

    nombreProducto = forms.CharField(
        validators=[nombre_validator],
        min_length=3,
        max_length=50,
        error_messages={
            "required": "El nombre del producto es obligatorio",
            "min_length": "El nombre debe tener al menos 3 caracteres",
            "max_length": "El nombre no puede exceder 50 caracteres",
        },
    )

    costoProducto = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            "required": "El costo es obligatorio",
            "min_value": "El costo debe ser mayor a 0",
            "invalid": "Ingrese un número válido con máximo 2 decimales",
        },
    )

    precioVenta = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        error_messages={
            "required": "El precio de venta es obligatorio",
            "min_value": "El precio debe ser mayor a 0",
        },
    )

    stockActual = forms.IntegerField(
        min_value=0,
        max_value=9999,
        error_messages={
            "required": "El stock actual es obligatorio",
            "min_value": "El stock no puede ser negativo",
            "max_value": "El stock no puede exceder 9999 unidades",
        },
    )

    stockUmbral = forms.IntegerField(
        min_value=1,
        error_messages={
            "required": "El stock mínimo es obligatorio",
            "min_value": "El stock mínimo debe ser mayor a 0",
        },
    )

    imagen = forms.ImageField(
        required=False,
        error_messages={"invalid_image": "El archivo debe ser una imagen válida"},
    )

    class Meta:
        model = Producto
        fields = [
            "nombreProducto",
            "idCategoria",
            "costoProducto",
            "precioVenta",
            "stockActual",
            "stockUmbral",
            "imagen",
        ]

    def clean(self):
        cleaned_data = super().clean()
        costo = cleaned_data.get("costoProducto")
        precio = cleaned_data.get("precioVenta")
        stock_actual = cleaned_data.get("stockActual")
        stock_umbral = cleaned_data.get("stockUmbral")
        imagen = cleaned_data.get("imagen")

        # Validar margen de ganancia
        if costo and precio:
            margen = ((precio - costo) / costo) * 100
            if margen < 10:
                raise forms.ValidationError(
                    "El margen de ganancia debe ser al menos del 10%"
                )

        # Validar que el precio sea mayor al costo
        if costo and precio and precio <= costo:
            raise forms.ValidationError("El precio de venta debe ser mayor al costo")

        # Validar que el stock umbral no sea mayor al stock actual
        if stock_actual is not None and stock_umbral is not None:
            if stock_umbral > stock_actual:
                raise forms.ValidationError(
                    "El stock mínimo no puede ser mayor al stock actual"
                )

        # Validar imagen
        if imagen:
            # Validar tamaño máximo (2MB)
            if imagen.size > 2 * 1024 * 1024:
                raise forms.ValidationError("La imagen no puede exceder 2MB")

            # Validar dimensiones
            img = Image.open(imagen)
            width, height = img.size
            if width > 1000 or height > 1000:
                raise forms.ValidationError(
                    "Las dimensiones de la imagen no pueden exceder 1000x1000 pixels"
                )
            if width < 100 or height < 100:
                raise forms.ValidationError(
                    "Las dimensiones de la imagen deben ser al menos 100x100 pixels"
                )

        return cleaned_data

    def clean_nombreProducto(self):
        nombre = self.cleaned_data.get("nombreProducto")
        # Validación adicional con regex
        if not re.match(r"^[a-zA-Z0-9\s]+$", nombre):
            raise forms.ValidationError(
                "El nombre solo puede contener letras, números y espacios"
            )

        # Verificar si existe otro producto con el mismo nombre
        if (
            Producto.objects.filter(nombreProducto=nombre)
            .exclude(id=self.instance.id if self.instance else None)
            .exists()
        ):
            raise forms.ValidationError("Ya existe un producto con este nombre")
        return nombre
