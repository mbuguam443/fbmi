from django.db import models
from members.models import Member
from finance.models import Transaction


class Giving(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank'),
        ('card', 'Card'),
        ('other', 'Other'),
    ]
    GIVING_CATEGORIES = [
        ('tithe', 'Tithe'),
        ('offering', 'Offering'),
        ('donation', 'Donation'),
        ('building_fund', 'Building Fund'),
        ('missions', 'Missions'),
        ('special_contribution', 'Special Contribution'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='givings', null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    giving_category = models.CharField(max_length=30, choices=GIVING_CATEGORIES)
    date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True, db_index=True)
    mpesa_merchant_request_id = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='giving_record')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        member_name = str(self.member) if self.member else 'Basket Offering'
        return f"{member_name} - {self.amount} - {self.date}"
