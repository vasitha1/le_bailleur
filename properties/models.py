from datetime import timedelta
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class Landlord(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=15,  blank=True)
    whatsapp_number = models.CharField(max_length=20, null=True, unique=True)
    
    def __str__(self):
        return self.name

class Property(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='properties')
    
    def __str__(self):
        return self.name

class RentEntity(models.Model):
    name = models.CharField(max_length=255)  # Can be whatever the landlord wants to rent out; room, apartment, condo, machine...
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rent_entities')
    
    def __str__(self):
        return f"{self.name} ({self.property.name})"

class Tenant(models.Model):
    rent_entity = models.ForeignKey(RentEntity, null=True, on_delete=models.CASCADE, related_name='tenants')
    name = models.CharField(max_length=200)
    whatsapp_number = models.CharField(max_length=20, unique=True)
    start_of_payment_cycle = models.DateField()
    bills_due_date = models.DateField()
    last_rent_paid = models.DateField(null=True, blank=True)
    last_bill_paid = models.DateField(null=True, blank=True)
    payment_cycle_months = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return self.name
    
    def calculate_actual_due_date(self):
        """Calculate the actual due date based on the payment cycle."""
        # Calculate the actual due date by adding the payment cycle months to the start of the payment cycle
        return self.start_of_payment_cycle + relativedelta(months=self.payment_cycle_months)
    
    def is_rent_due(self):
        """Check if rent is due based on the current date."""
        actual_due_date = self.calculate_actual_due_date()
        return actual_due_date <= timezone.now().date()
    
    def is_bills_due(self):
        """Check if bills are due based on the current date."""
        return self.bills_due_date <= timezone.now().date()

class PaymentReceipt(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='receipts')
    payment_date = models.DateField(auto_now_add=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    months_paid = models.PositiveIntegerField(default=1)
    receipt_number = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.tenant.name}"

class Session(models.Model):
    """Track user session and conversation state in WhatsApp."""
    whatsapp_number = models.CharField(max_length=20, unique=True)
    is_landlord = models.BooleanField(null=True, blank=True)  # None if not determined yet
    current_state = models.CharField(max_length=100)  # The current state in the conversation flow
    last_activity = models.DateTimeField(auto_now=True)
    context_data = models.JSONField(default=dict, blank=True)  # Store temporary data during conversation
    
    def __str__(self):
        return f"Session for {self.whatsapp_number}"
    
    def is_expired(self):
        """Check if the session has been inactive for more than 10 minutes."""
        return (timezone.now() - self.last_activity) > timedelta(minutes=10)