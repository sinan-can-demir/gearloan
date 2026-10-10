from django.urls import path

from .views import ItemTypeDetailView, ItemTypeListView

app_name = "inventory"

urlpatterns = [
    path("", ItemTypeListView.as_view(), name="item_list"),
    path("<int:pk>/", ItemTypeDetailView.as_view(), name="item_detail"),
]
