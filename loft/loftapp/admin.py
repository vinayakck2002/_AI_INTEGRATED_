from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Product)
admin.site.register(ShoeCategory)
admin.site.register(Cart)
admin.site.register(Gender)
admin.site.register(ProductSize)


