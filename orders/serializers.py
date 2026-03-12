from rest_framework import serializers
from .models import Product, Inventory, Dealer, Order, OrderItem

class ProductSerializer(serializers.ModelSerializer):
    stock_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'sku', 'description', 'price', 'stock_quantity', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_stock_quantity(self, obj):
        #return 0 if inventory doesnot exist yet
        try:
            return obj.inventory.quantity
        except:
            return 0

class InventorySerializer(serializers.ModelSerializer):
    #showing product name alongside inventory info
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = ['id', 'product', 'product_name', 'quantity', 'updated_at']
        read_only_fields = ['updated_at']


class OrderSummarySerializer(serializers.ModelSerializer):
    #summary of order ofr dealer detail view
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'status', 'total_amount', 'created_at']

class DealerSerializer(serializers.ModelSerializer):
    orders = OrderSummarySerializer(many=True, read_only= True)

    class Meta:
        model = Dealer
        fields = ['id', 'name', 'email', 'phone', 'address', 'orders', 'created_at']
        read_only_fields = ['created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    #showing product name in response so it will be more readable
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'line_total']
        read_only_fields = ['line_total']

class OrderSerializer(serializers.ModelSerializer):
    #all item inside the order
    items = OrderItemSerializer(many=True)
    #dealer name in response
    dealer_name = serializers.CharField(source='dealer.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'dealer', 'dealer_name',
            'status', 'total_amount', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'status', 'total_amount', 'created_at', 'updated_at']

    
    def create(self, validated_data):
        #pulling out items data before creating order

        items_data = validated_data.pop('items')

        #create the order first
        order = Order.objects.create(**validated_data)

        #now we create each order item one by one
        for item in items_data:
            OrderItem.objects.create(order=order, **item)

        total = sum(i.line_total for i in order.items.all())
        order.total_amount = total
        order.save()

        return order
    
    def update(self, instance, validated_data):
        #don't allow editing confirmed or delivered orders
        if instance.status  in ['Confirmed', 'Delivered']:
            raise serializers.ValidationError("Cannot edit a confirmed or delivered order.")
        
        items_data = validated_data.pop('items', None)

        #update basic orders fields
        instance.dealer = validated_data.get('dealer', instance.dealer)
        instance.save()

        #if items are provided, replace old items with new ones
        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                OrderItem.objects.create(order=instance, **item)

        #recalculate total
        total = sum(i.line_total for i in instance.items.all())
        instance.total_amount = total
        instance.save()

        return instance

