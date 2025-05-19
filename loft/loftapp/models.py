from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .constants import PaymentStatus
from django.db.models.fields import CharField
from django.utils import timezone

class ShoeCategory(models.Model):
    name = models.CharField(max_length=250)
    def __str__(self):
        return self.name

class Gender(models.Model):
    name = models.CharField(max_length=250)

class Product(models.Model):    
    name= models.CharField(max_length=250)
    price= models.IntegerField()
    offerprice= models.IntegerField()
    color= models.CharField(max_length=250)
    image= models.ImageField(upload_to='product/')
    image1= models.ImageField(upload_to='product/',null=False, default='')
    image2= models.ImageField(upload_to='product/',null=False, default='')
    image3= models.ImageField(upload_to='product/',null=False, default='')
    image4= models.ImageField(upload_to='product/',null=False, default='')
    image5= models.ImageField(upload_to='product/',null=False, default='')
    description= models.TextField()
    shoe_category= models.ForeignKey(ShoeCategory, on_delete=models.CASCADE,null=True)
    priority = models.IntegerField(default=0)#ITEM SEASON WISE CHANGE EG: CHRISMAS, DIWALI. ONAM
    gender= models.ForeignKey(Gender, on_delete=models.CASCADE,null=True)
    rating=models.FloatField(default=0)
    vector_data=models.TextField(null=True)

    def __str__(self):
        return self.name
    
class users(models.Model):
    name=models.ForeignKey(User,on_delete=models.CASCADE)
    vector_data=models.TextField(null=True)
    def __str__(self):
        return self.name.username
    
class SearchHistory(models.Model):
    query = models.CharField(max_length=255)
    user = models.ForeignKey(users, on_delete=models.CASCADE)

class ViewHistory(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    user=models.ForeignKey(users,on_delete=models.CASCADE)
    
class ProductSize(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='sizes')
    size= models.IntegerField()
    Stock=models.IntegerField()
    @property
    def total_price(self):
        return self.product.price * self.quantity
    


class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True, blank=True)  
    quantity= models.IntegerField(default=1)
    totalprice=models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name=models.CharField(max_length=225)
    address=models.TextField()
    phone=models.CharField(max_length=12)

    

class Buy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)#product delete order should be keep thats why SET_NULL
    address = models.ForeignKey(Address,on_delete=models.CASCADE,null=True,blank=True)
    quantity= models.IntegerField(default=1)
    price= models.IntegerField()
    date = models.DateField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
     
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Assuming you have a Product model
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate entries
        
    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.name}"
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    amount = models.FloatField(_("Amount"), null=False, blank=False)
    status = models.CharField(
        _("Payment Status"),
        default=PaymentStatus.PENDING,
        max_length=254,
        blank=False,
        null=False,
    )
    provider_order_id = models.CharField(_("Order ID"), max_length=40,null=True)
    payment_id = models.CharField(_("Payment ID"), max_length=36,null=True)
    signature_id = models.CharField(_("Signature ID"), max_length=128,null=True)
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.quantity})"


class reviews(models.Model):
    rating=models.IntegerField()
    description=models.TextField()
    uname=models.ForeignKey(users,on_delete=models.CASCADE)
    pname=models.ForeignKey(Product,on_delete=models.CASCADE)

    


