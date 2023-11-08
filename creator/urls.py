from django.urls import path
from . import views
from . import admin
app_name='creator'

urlpatterns = [
	path('<str:name>/', views.index, name="index"),
	# path('index', views.index, name='index'),
	path('<str:name>/index', views.index, name='index'),
	path('<str:name>/info', views.info, name='info'),
	path('<str:name>/task_create', views.task_create, name='task_create'),
	path('<str:name>/task_update', views.task_update, name='task_update'),
	path('<str:name>/task_list', views.task_list, name='task_list'),
	path('<str:name>/task_search', views.task_search, name='task_search'),
	path('<str:name>/other_info', views.other_info, name="other_info"),
	path('<str:name>/problem_create', views.problem_create, name="problem_create"),
	path('<str:name>/task_info', views.task_info, name="task_info"),
	path('<str:name>/check', views.check, name="task_info"),
	path('<str:name>/charts', views.charts, name="charts"),
	path('<str:name>/info_change', views.info_change, name="info_change"),
	path('<str:name>/<str:taskId>/labelResult', views.labelResult, name="labelResult"),
	path('<str:name>/<str:taskId>/getlink/', views.getlink),
	path('<str:name>/<str:taskId>/labelResultDownload/', views.labelResultDownload, name="labelResultDownload"),
]