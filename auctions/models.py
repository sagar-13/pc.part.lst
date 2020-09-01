from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
from django.db.models import Max
import logging
logger = logging.getLogger(__name__)
class User(AbstractUser):
    watchlist = models.ManyToManyField('Listing', blank=True, related_name="watched")


# model for auction listings 
class Listing(models.Model):
    active = models.BooleanField(default=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=1000)
    starting = models.IntegerField()
    url = models.CharField(max_length=500)
    category = models.CharField(max_length=64)
   
   
    def __str__(self):

        return f"{self.title} in {self.category} by {self.user} - {self.starting}"
    @property
    def recent_bids(self):
        
        last_ten = self.all_bids.all().order_by('-id')[:5]
        last_ten_in_ascending_order = reversed(last_ten)
        return last_ten_in_ascending_order
     
    @property
    def top_bid(self):  
        return self.all_bids.all().aggregate(Max('amount'))["amount__max"]
    

# model for bids 
class Bid(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="bids")
    listing = models.ForeignKey(Listing,on_delete=models.CASCADE, related_name="all_bids")
    amount = models.IntegerField(default=0)
    date = models.DateTimeField(default=now)
    
    def save(self, *args, **kwargs):
        if self.amount == 0:
            self.amount = self.listing.starting
        super(Bid, self).save(*args, **kwargs)
    def __str__(self):

        return f"{self.amount} by {self.user}"
    

# model for comments made on auctions 
class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments_for")
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="comments_by")
    content = models.CharField(default="",max_length=500)
    date = models.DateTimeField(default=now)

