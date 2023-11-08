from django.urls import path
from . import views
from . import admin
app_name='worker'

urlpatterns = [
	path('<str:name>/', views.index, name="index"),
	# path('index', views.index, name='index'),
	path('<str:name>/index', views.index, name='index'),
	path('<str:name>/info', views.info, name='info'),
	path('<str:name>/task_list', views.task_list, name='task_list'),
	path('<str:name>/charts', views.charts, name='charts'),
	path('<str:name>/other_info', views.other_info, name="other_info"),
	path('<str:name>/task_info', views.task_info, name="task_info"),
	path('<str:name>/task_accept', views.task_accept, name="task_accept"),
	path('<str:name>/task_submit', views.task_submit, name="task_submit"),
	path('<str:name>/task_abandon', views.task_abandon, name="task_abandon"),
	path('<str:name>/labelTry', views.labelTry, name="labelTry"),
	path('<str:name>/problem_create', views.problem_create, name="problem_create"),
	path('<str:name>/label', views.label, name="label"),
	path('<str:name>/getlink/', views.getlink),
]