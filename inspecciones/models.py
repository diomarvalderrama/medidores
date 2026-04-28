from django.db import models


class RegistroInspeccion(models.Model):
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_finalizacion = models.TimeField()
    correo = models.EmailField()
    nombre_inspector = models.CharField(max_length=150)
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
    observaciones = models.TextField()

    foto_1 = models.ImageField(upload_to='medidores/', blank=True, null=True)
    foto_2 = models.ImageField(upload_to='medidores/', blank=True, null=True)
    foto_3 = models.ImageField(upload_to='medidores/', blank=True, null=True)
    foto_4 = models.ImageField(upload_to='medidores/', blank=True, null=True)

    def __str__(self):
        return self.serial


class InformeTecnico(models.Model):
    fecha_informe = models.DateField(auto_now_add=True)
    medidores = models.ManyToManyField(Medidor)
    generado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Informe {self.id}"