from django.urls import path
from . import views

urlpatterns = [
    #product endpoints
    path('products/', views.ProductListView.as_view()),
    path('products/<int:pk>/', views.ProductDetailView.as_view()),

    #dealer endpoints
    path('dealers/', views.DealerListView.as_view()),
    path('dealers/<int:pk>/', views.DealerDetailView.as_view()),

    #inventory endpoints
    path('inventory/', views.InventoryListView.as_view()),
    path('inventory/<int:product_id>/', views.InventoryDetailView.as_view()),

    #order endpoints
    path('orders/', views.OrderListView.as_view()),
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
    path('orders/<int:pk>/confirm/', views.OrderConfirmView.as_view()),
    path('orders/<int:pk>/deliver/', views.OrderDeliverView.as_view()),
    path('orders/<int:pk>/summary/', views.OrderSummaryView.as_view()),
]
