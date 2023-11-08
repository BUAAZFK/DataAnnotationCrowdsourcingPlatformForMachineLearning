from django.urls import path
from . import views
from . import admin
app_name='manager'

urlpatterns = [
    path('', views.index, name="index"),
    path('index', views.index, name="index"),
    path('staff_manage', views.staff_manage, name="staff_manage"),
    path('user_manage', views.user_manage, name="user_manage"),
    path('staff_add', views.staff_add, name="staff_add"),
    path('staff_update', views.staff_update, name="staff_update"),
    path('staff_delete', views.staff_delete, name="staff_delete"),
    path('notice', views.notice, name="notice"),
    path('notice_update', views.notice_update, name="notice_update"),
    path('notice_delete', views.notice_delete, name="notice_delete"),
]