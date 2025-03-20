from rest_framework import serializers
from .models import Property, Tenant, Landlord, RentEntity, PaymentReceipt, Session

class LandlordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landlord
        fields = '__all__'

class PropertySerializer(serializers.ModelSerializer):
    landlord_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = '__all__'
    
    def get_landlord_name(self, obj):
        return obj.landlord.name if obj.landlord else None

class RentEntitySerializer(serializers.ModelSerializer):
    property_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RentEntity
        fields = '__all__'
    
    def get_property_name(self, obj):
        return obj.property.name if obj.property else None

class TenantSerializer(serializers.ModelSerializer):
    rent_entity_name = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()
    landlord_name = serializers.SerializerMethodField()
    rent_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = '__all__'
    
    def get_rent_entity_name(self, obj):
        return obj.rent_entity.name if obj.rent_entity else None
    
    def get_property_name(self, obj):
        return obj.rent_entity.property.name if obj.rent_entity and obj.rent_entity.property else None
    
    def get_landlord_name(self, obj):
        return obj.rent_entity.property.landlord.name if obj.rent_entity and obj.rent_entity.property and obj.rent_entity.property.landlord else None
    
    def get_rent_status(self, obj):
        return "Due" if obj.is_rent_due() else "Not Due"

class PaymentReceiptSerializer(serializers.ModelSerializer):
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentReceipt
        fields = '__all__'
    
    def get_tenant_name(self, obj):
        return obj.tenant.name if obj.tenant else None

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'