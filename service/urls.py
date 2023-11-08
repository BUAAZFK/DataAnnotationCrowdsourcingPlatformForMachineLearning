from django.urls import path
from . import views
from . import admin
app_name='service'

urlpatterns = [
	path('', views.index, name="index"),
	path('<str:sId>/index', views.index, name="index"),
	path('<str:sId>/task_list', views.task_list, name="task_list"),
	path('<str:sId>/<int:taskId>/check', views.check, name="check"),
	path('<str:sId>/task_info', views.task_info, name="task_info"),
	path('<str:sId>/<int:pId>/handle', views.handle, name="handle"),
	path('<str:sId>/<str:taskId>/labelResultView', views.labelResultView, name="labelResultView"),
	path('<str:sId>/<str:taskId>/getlink/', views.getlink),
]