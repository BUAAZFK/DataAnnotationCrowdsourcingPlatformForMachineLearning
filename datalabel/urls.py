"""datalabel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='login'),
    path('index', views.index, name='login'),
    path('notice', views.notice, name='notice'),
    path('jiaocheng', views.jiaocheng, name='jiaocheng'),
    path('task_detail', views.task_detail, name='task_detail'),
    path('notice_info', views.notice_info, name='notice_info'),
    path('login', views.login, name='login'),
    path('admin_login', views.admin_login, name='admin_login'),
    path('register', views.register, name='register'),
    path('logout', views.logout, name='logout'),
    path('comment', views.comment, name='comment'),
    path('creator/', include('creator.urls')),
    path('worker/', include('worker.urls')),
    path('service/', include('service.urls')),
    path('finance/', include('finance.urls')),
    path('manager/', include('manager.urls')),
    path('admin/', admin.site.urls),
]
