from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Inventory, Order, Dealer
from .serializers import ProductSerializers, InventorySerializers, DealerSerializers, OrderSerializers

#product views

class ProductListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializers(products, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ProductSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProductDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializers(product)
        return Response(serializer.data)
    
    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializers(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response({"message": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


#dealer view
class DealerListView(APIView):
    def get(self, request):
        dealers = Dealer.objects.all()
        serializer = DealerSerializers(dealers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = DealerSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class DealerDetailView(APIView):
    def get(self, request, pk):
        dealer = get_object_or_404(Dealer, pk=pk)
        serializer = DealerSerializers(dealer)
        return Response(serializer.data)
    
    def put(self, request, pk):
        dealer = get_object_or_404(Dealer, pk=pk)
        serializer = DealerSerializers(dealer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class InventoryListView(APIView):
    def get(self, request):
        inventory = Inventory.objects.select_related('product').all()
        serializer = InventorySerializers(inventory, many=True)
        return Response(serializer.data)
    

class InventoryDetailView(APIView):
    def put(self, request, product_id):
        #get inventory by product id
        inventory = get_object_or_404(Inventory, product_id=product_id)
        serializer = InventorySerializers(inventory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#order views
class OrderListView(APIView):
    def get(self, request):
        orders = Order.objects.prefetch_related('items').all()
        serializer = OrderSerializers(orders, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = OrderSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class OrderDetailView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderSerializers(order)
        return Response(serializer.data)

    def put(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderSerializers(order, data=request.data)
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
        
        order.status = 'Confirmed'
        order.save()
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
