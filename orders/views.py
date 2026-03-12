from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from .models import Product, Inventory, Order, Dealer
from .serializers import ProductSerializer, InventorySerializer, DealerSerializer, OrderSerializer
from django.db import transaction
from django.db.models import ProtectedError

#product views

class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProductDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    
    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            product.delete()
            return Response({"message": "Product deleted successfully."}, 
            status=status.HTTP_204_NO_CONTENT
            )
        except ProtectedError:
            return Response(
                {"error": "Cannot delete this product because it has existing orders."},
                status=status.HTTP_400_BAD_REQUEST
            )


#dealer view
class DealerListView(APIView):
    def get(self, request):
        dealers = Dealer.objects.all()
        serializer = DealerSerializer(dealers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = DealerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DealerDetailView(APIView):
    def get(self, request, pk):
        dealer = get_object_or_404(Dealer, pk=pk)
        serializer = DealerSerializer(dealer)
        return Response(serializer.data)
    
    def put(self, request, pk):
        dealer = get_object_or_404(Dealer, pk=pk)
        serializer = DealerSerializer(dealer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        dealer = get_object_or_404(Dealer, pk=pk)
        try:
            dealer.delete()
            return Response({"message": "Dealer deleted successfully."})
        except Exception:
            #if dealer has orders, PROTECT will block deletion
            return Response(
                {"error": "Cannot delete dealer with existing orders."},
                status=status.HTTP_400_BAD_REQUEST
            )
    

class InventoryListView(APIView):
    def get(self, request):
        inventory = Inventory.objects.select_related('product').all()
        serializer = InventorySerializer(inventory, many=True)
        return Response(serializer.data)
    

class InventoryDetailView(APIView):
    def put(self, request, product_id):
        #get inventory by product id
        inventory = get_object_or_404(Inventory, product_id=product_id)
        data = {'quantity': request.data.get('quantity', inventory.quantity)}

        serializer = InventorySerializer(inventory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#order views
class OrderListView(APIView):
    def get(self, request):
        orders = Order.objects.prefetch_related('items').all()
        
        #filter by status if provided /api/orders/?status=Draft
        status_filter = request.query_params.get('status', None)
        if status_filter:
            orders = orders.filter(status=status_filter)

        #filter by dealer if provided /api/orders/?dealer_id=1
        dealer_id = request.query_params.get('dealer_id', None)
        if dealer_id:
            orders = orders.filter(dealer_id=dealer_id)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OrderDetailView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        
        #block editing confirmed or delivered orders at view level too
        if order.status in ['Confirmed', 'Delivered']:
            return Response(
                {"error": f"Cannot edit an order with status '{order.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OrderConfirmView(APIView):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        #only draft order can be confirmed
        if order.status != 'Draft':
            return Response(
                {"error": "Only Draft orders can be confirmed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #checking if order has any items
        if not order.items.exists():
            return Response(
                {"error": "Cannot confirm an empty order."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #if anything fails, nothing get saved
        try:
            with transaction.atomic():
                for item in order.items.all():
                    #get inventory for this product
                    try:
                        inventory = Inventory.objects.select_for_update().get(product=item.product)
                    except Inventory.DoesNotExist:
                        raise ValidationError(
                            f"No inventory record found for product '{item.product.name}'.")
                    
                    #check if enough stock is available
                    if inventory.quantity < item.quantity:
                        raise ValidationError(
                            f"Not enough stock for '{item.product.name}'."
                            f"Available: {inventory.quantity}, Required: {item.quantity}."
                        )
                    
                    #deduct stock
                    inventory.quantity -= item.quantity
                    inventory.save()

                order.status = 'Confirmed'
                order.save()

        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Order confirmed successfully."})
    
class OrderDeliverView(APIView):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        #only confirmed order can be delivered
        if order.status != 'Confirmed':
            return Response(
                {"error": "Only Confirmed order can marked as delivered."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'Delivered'
        order.save()
        return Response({"message": "Order marked as delivered successfully."})

class OrderSummaryView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        items = order.items.all()

        summary = {
            "order_number": order.order_number,
            "dealer": order.dealer.name,
            "status": order.status,
            "total_items": items.count(),
            "items": [
                {
                    "product": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total
                }
                for item in items
            ],
            "created_at": order.created_at,
        }
        return Response(summary)