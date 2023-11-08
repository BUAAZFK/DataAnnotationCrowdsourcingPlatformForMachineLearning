from django.urls import path
from . import views
from . import admin
app_name='finance'

urlpatterns = [
	path('', views.index, name="index"),
	path('<str:fId>/index', views.index, name="index"),
	path('<str:fId>/task_list', views.task_list, name="task_list"),
	path('<str:fId>/<str:taskId>/check', views.check, name="check"),

]