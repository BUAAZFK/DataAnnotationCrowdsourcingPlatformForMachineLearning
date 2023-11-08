import base64
import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect,reverse
from creator import models as cmodels
from worker import models as wmodels
from service import models as smodels
from finance import models as fmodels
from manager import models as mmodels
from django.contrib.auth.decorators import login_required
# Create your views here.
def index(request):
    userName = request.COOKIES.get('userName')
    notices = mmodels.notice.objects.filter(deleted=0, public=True)
    type = request.COOKIES.get('type')
    if request.method=="GET":
        print('index-userName:', userName, ' userType:', type)
        # 进行任务筛选
        taskType = request.GET.get('taskType')
        if taskType:
            tasks = cmodels.task.objects.filter(status='unAccept', deleted=0, taskType=taskType)
        else:
            tasks = cmodels.task.objects.filter(status='unAccept', deleted=0)
        for task in tasks:
            if task.cover:
                image_base4 = base64.b64encode(task.cover).decode('utf8')
                task.data = image_base4
        return render(request, "index.html", {'name':userName, 'type':type, 'tasks':tasks, 'notices':notices})
    elif request.method=="POST":
        taskKey = request.POST.get('taskKey')
        tasks = cmodels.task.objects.filter(status='unAccept', deleted=0, taskName__icontains=taskKey)
        for task in tasks:
            if task.cover:
                image_base4 = base64.b64encode(task.cover).decode('utf8')
                task.data = image_base4
        return render(request, "index.html", {'name':userName, 'type':type, 'tasks':tasks, 'notices':notices})


def jiaocheng(request):
    userName = request.COOKIES.get('userName')
    type = request.COOKIES.get('type')
    return render(request, 'jiaocheng.html', {'name':userName, 'type':type})

def task_detail(request):
    taskId = request.GET.get('taskId')
    task = cmodels.task.objects.get(taskId=taskId)
    userName = request.COOKIES.get('userName')
    type = request.COOKIES.get('type')
    return render(request, 'task_detail.html', {'task':task, 'name':userName, 'type':type})

def login(request):
    # 如果是get请求，返回登录界面过去
    userName = request.COOKIES.get('userName')
    if userName:
        type = request.COOKIES.get('type')
        if type=="creator":
            name = cmodels.creator.objects.get(name=userName).name
        elif type=="worker":
            name = wmodels.worker.objects.get(name=userName).name
        return redirect(f'/', {'name':userName, 'type':type})
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        userName = request.POST.get('email')
        pwd = request.POST.get('password')
        remember = request.POST.get('remember')
        # 获取数据库中的用户名密码
        flag = 0
        type = "creator"
        try:
            res1 = wmodels.worker.objects.get(name = userName)
            flag = 1
        except:
            pass
        try:
            res2 = cmodels.creator.objects.get(name=userName)
            flag = 2
        except:
            pass
        # 如果没有查询到数据，返回用户名不存在
        if flag==0:
            return render(request, 'login.html', {'msg':'用户名不存在'})
        elif flag==2:
            type = "creator"
            if res2.pwd != pwd:
                return render(request, 'login.html', {'msg':'密码错误'})
            name = res2.name
            response = redirect(f'/', {'name':name, 'type':type})
            response.set_cookie('type', type)
            response.set_cookie('userName', userName)
            response.set_cookie('pwd', pwd)
            return response
        elif flag==1:
            type = "worker"
            if res1.pwd != pwd:
                return render(request, 'login.html', {'msg':'密码错误'})
            name = res1.name
            response = redirect(f'/', {'name':name, 'type':type})
            response.set_cookie('type', type)
            response.set_cookie('userName', userName)
            response.set_cookie('pwd', pwd)
            return response

def admin_login(request):
    if request.method=="GET":
        return render(request, "admin_login.html")
    elif request.method=="POST":
        userId = request.POST.get('id')
        pwd = request.POST.get('pwd')
        type = request.POST.get('type')
        if type=='servicer':
            user = mmodels.staff.objects.get(staffId=userId)
            if user:
                if pwd!=user.pwd:
                    return render(request, 'admin_login.html', {'msg': '密码错误'})
                else:
                    return redirect(f'service/{userId}/index')
            else:
                return render(request, 'admin_login.html', {'msg':'用户不存在'})
        elif type=='financer':
            user = mmodels.staff.objects.get(staffId=userId)
            if user:
                if pwd!=user.pwd:
                    return render(request, 'admin_login.html', {'msg': '密码错误'})
                else:
                    return redirect(f'finance/{userId}/index')
            else:
                return render(request, 'admin_login.html', {'msg':'用户不存在'})
        elif type=='manager':
            try:
                manager = mmodels.manager.objects.get(mId=userId)
                if pwd!=manager.pwd:
                    return render(request, 'admin_login.html', {'msg':'密码错误'})
                else:
                    return redirect('manager/index')
            except:
                return render(request, 'admin_login.html', {'msg':'用户不存在'})

def register(request):
    # 如果是get请求，返回登录界面过去
    if request.method == 'GET':
        print('q')
        return render(request, 'register.html')
    elif request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        type = request.POST.get('type')
        # 获取数据库中的用户名密码
        res = wmodels.worker.objects.filter(email = email)
        res2 = cmodels.creator.objects.filter(email=email)
        # 如果没有查询到数据，返回用户名不存在
        if len(res) != 0 or len(res2)!=0:
            print('邮箱已被注册！')
            return redirect('login')
        if type=="任务接受者":
            worker = wmodels.worker.objects.create(
                name = name,
                email=email,
                pwd=password,
                phone=phone
            )
            worker.save()
            context = {'用户名':name}
            response = redirect(f'/', {'name':name, 'type':type})
            response.set_cookie('type', "worker")
            response.set_cookie('userName', name)
            response.set_cookie('pwd', password)
            return response
        elif type=="任务发布者":
            creator = cmodels.creator.objects.create(
                name=name,
                email=email,
                pwd=password,
                phone=phone
            )
            creator.save()
            context = {'用户名': name}
            print(name)
            response = redirect(f'/', {'name':name, 'type':type})
            response.set_cookie('type', "creator")
            response.set_cookie('userName', name)
            response.set_cookie('pwd', password)
            return response

def logout(request):
    response = redirect('/')
    response.delete_cookie('type')
    response.delete_cookie('userName')
    response.delete_cookie('pwd')
    return response

def comment(request):
    name = request.POST.get('name')
    wId = wmodels.worker.objects.get(name=name).wId
    taskId = request.POST.get('taskId')
    origin_url = request.META.get('HTTP_REFERER')
    content = request.POST.get('comment')
    task = cmodels.task.objects.get(taskId=taskId)
    new_comment = wmodels.comment(
        cId_id=task.cId_id,
        wId_id=wId,
        taskId_id = taskId,
        content = content,
        cmTime = datetime.datetime.now(),
        promoter='worker' if 'worker' in origin_url else 'creator'
    )
    new_comment.save()
    if 'worker' in origin_url:
        return redirect(f'/worker/{name}/task_info?taskId={taskId}')
    else:
        return redirect(f'/creator/{name}/task_info?taskId={taskId}')

def notice(request):
    userName = request.COOKIES.get('userName')
    type = request.COOKIES.get('type')
    notices = mmodels.notice.objects.filter(deleted=0, public=True)
    return render(request,'notice.html', {'notices':notices, 'name':userName, 'type':type})

def notice_info(request):
    if request.method=="GET":
        nId = request.GET.get('nId')
        notice = mmodels.notice.objects.get(nId=nId)
        return render(request, 'notice_info.html', {'notice':notice})