from datetime import timedelta  
from django.db import models  
from django.utils import timezone  
from dateutil.relativedelta import relativedelta

class Landlord(models.Model):  
    name = models.CharField(max_length=255)  
    email = models.EmailField()  
    phone_number = models.CharField(max_length=15)  

    def __str__(self):  
        return self.name  

class Property(models.Model):  
    name = models.CharField(max_length=200)  
    address = models.TextField()  
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='properties')  

    def __str__(self):  
        return self.name  

class RentEntity(models.Model):
    name = models.CharField(max_length=255) #Can be what ever he wants to rent out; room, appartment, condo, machine....
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rent_entity')

class Tenant(models.Model):  
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tenants')  
    name = models.CharField(max_length=200)  
    whatsapp_number = models.CharField(max_length=20)    
    start_of_payment_cycle = models.DateField()  # The date when the current payment cycle starts  
    bills_due_date = models.DateField()  # Bills due date  
    last_rent_paid = models.DateField(null=True, blank=True)  # Last rent payment date  
    last_bill_paid = models.DateField(null=True, blank=True)  # Last bill payment date  
    payment_cycle_months = models.PositiveIntegerField(default=1)  # Number of months for which rent has been paid  

    def __str__(self):  
        return self.name  

    def calculate_actual_due_date(self):  
        """Calculate the actual due date based on the payment cycle."""  
        # Calculate the actual due date by adding the payment cycle months to the start of the payment cycle  
        return self.start_of_payment_cycle + relativedelta(months=self.payment_cycle_months)  

    def is_rent_due(self):  
        """Check if rent is due based on the current date."""  
        actual_due_date = self.calculate_actual_due_date()  # Calculate the actual due date  
        return actual_due_date <= timezone.now().date()  # Check if the actual due date has passed  

    def is_bills_due(self):  
        """Check if bills are due based on the current date."""  
        return self.bills_due_date <= timezone.now().date()  # Check if bills are due  