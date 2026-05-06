from django.db import models


class RegistroInspeccion(models.Model):
    fecha = models.DateField()
    conclusiones_generales = models.TextField()

    def __str__(self):
        return f"Registro {self.id} - {self.fecha}"


class Medidor(models.Model):
    ESTADOS = [
        ('BUENO', 'Bueno'),
        ('REGULAR', 'Regular'),
        ('MALO', 'Malo'),
        ('DETERIORADO', 'Deteriorado'),
        ('FUERA_SERVICIO', 'Fuera de servicio'),
        ('USADO', 'Usado'),
    ]

    ALTERACION_CHOICES = [
        ('SI', 'Sí'),
        ('NO', 'No'),
    ]

    registro = models.ForeignKey(
        RegistroInspeccion,
        on_delete=models.CASCADE,
        related_name='medidores'
    )

    serial = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    anio = models.IntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS)
    codigo = models.CharField(max_length=100)

    medidor_con_alteracion = models.CharField(
        max_length=2,
        choices=ALTERACION_CHOICES,
        default='NO'
    )

    observaciones_encontradas = models.TextField()

    foto_1 = models.ImageField(upload_to='medidores/', blank=True, null=True)
    foto_2 = models.ImageField(upload_to='medidores/', blank=True, null=True)
    foto_3 = models.ImageField(upload_to='medidores/', blank=True, null=True)
    foto_4 = models.ImageField(upload_to='medidores/', blank=True, null=True)

    def __str__(self):
        return self.serial


class InformeTecnico(models.Model):
    fecha_informe = models.DateField()
    fecha_despiece = models.DateField()

    medidores = models.ManyToManyField(Medidor)
    generado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Informe {self.id}"