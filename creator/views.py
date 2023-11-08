import base64
import datetime
import io
import os
import zipfile
from itertools import chain
import json
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.core.paginator import Paginator
from django.core import serializers
from creator import models as cmodels
from worker import models as wmodels
from service import models as smodels
from finance import models as fmodels
from manager import models as mmodels
import paramiko
from django.contrib.auth.decorators import login_required


# Create your views here.


def index(request, name):
    '''
    该函数获取当前任务发布者发布的任务中所有被接受的任务的任务状态并显示到首页
    '''
    # 获取当前任务发布者被接受任务的任务状态
    # 获取当前用户的ID
    cId = cmodels.creator.objects.get(name=name).cId
    released_tasks = cmodels.task.objects.filter(cId=cId, deleted=0)
    released_task_ids = [item.taskId for item in released_tasks]
    # 获取所有被接受的任务
    tasks = wmodels.acceptedTask.objects.filter(delete=0)
    # 过滤出该用户发布的任务
    acceptedTasks = []
    for task in tasks:
        # 判断当前任务是否属于该用户发布的任务
        if task.taskId_id not in released_task_ids:
            continue
        # 为当前任务添加属性
        try:
            task.taskName = task.taskId.taskName
            task.workerName = task.wId.name
            acceptedTasks.append(task)
            len_of_project = len(cmodels.data.objects.filter(taskId_id=int(task.taskId_id)))
            len_of_label = len(wmodels.labels.objects.filter(taskId_id=int(task.taskId_id)))
            task.progress = int(len_of_label / len_of_project * 100)
        except:
            continue
    comments = wmodels.comment.objects.filter(cId_id=cId)
    for comment in comments:
        comment.taskName = comment.taskId.taskName
        comment.taskStatus = comment.taskId.get_status_display()
    return render(request, "creator/index.html",
                  {'name': name, 'type': '任务发布者', 'tasks': acceptedTasks, 'comments': comments})


def task_create(request, name):
    '''
    该函数获取前端页面提交的任务创建请求，并根据前端页面提供的内容创建新的任务
    '''
    if request.method == "GET":
        return render(request, 'creator/task_create.html', {'name': name, 'type': '任务发布者'})
    elif request.method == "POST":
        # 获取前端提供的任务相关信息
        taskName = request.POST.get('taskName')
        taskContent = request.POST.get('taskContent')
        taskType = request.POST.get('taskType')
        taskLimit = request.POST.get('taskLimit')
        taskReward = request.POST.get('taskReward')
        taskDescription = request.FILES.get('taskDescription')
        taskDescription = taskDescription.read()
        cover = request.FILES.get('cover')
        cover = cover.read()
        cId = cmodels.creator.objects.get(name=name).cId

        # 新建task，creator账户下的
        task = cmodels.task(
            taskName=taskName,
            taskContent=taskContent,
            taskLimit=taskLimit,
            cover=cover,
            taskDescription=taskDescription,
            reward=taskReward,
            cId_id=cId,
            createTime=datetime.datetime.now(),
            taskType=taskType,
        )
        task.save()
        # 获取前端提供的数据链接，并将新建数据5
        dLink = request.POST.get('dLink')
        dataDescription = request.POST.get('dataDescription')
        # 获取前端上传的数据，先判断数据类型，将上传的zip文件并存储到数据库中
        file = request.FILES.get('file')
        fBytes = file.read()

        # 判断数据类型
        dType = 0
        excels = ['xlsx', 'xls', 'csv']

        with io.BytesIO(fBytes) as f:
            with zipfile.ZipFile(f, 'r') as zfile:
                fname = zfile.namelist()[0]
                ftype = fname.split('.')[-1]
                if ftype in excels:
                    dType = 'word'
                else:
                    dType = 'pic'

        if dType == "pic":
            pictures = []
            # 将图片存储到数据库中
            with io.BytesIO(fBytes) as f:
                with zipfile.ZipFile(f, 'r') as zfile:
                    for fname in zfile.namelist():
                        with zfile.open(fname, mode='r') as tfile:
                            img = tfile.read()
                            pictures.append(img)
        # 将任务需求文件保存到云服务器上
        # 将任务需求文件保存到本地临时文件夹中
        # path = fr"D:\学习\大三\大三下\信息系统\project\2023-06-04-3\datalabel\statics\temp\{task.taskName}.pdf"
        path = f"./statics/temp/{task.taskName}.pdf"
        with open(path, 'wb') as file:
            file.write(task.taskDescription)
        task.taskDescriptionPath = f"/statics/temp/{task.taskName}.pdf"
        # 新建待发布任务审核任务，客服人员账户下的
        rctask = smodels.problem.objects.all()
        servicers = mmodels.staff.objects.filter(staffType='S', staffStatus='A', deleted=0)
        distribution = {}
        for servicer in servicers:
            distribution[servicer] = len(rctask.filter(staffId_id=servicer.staffId))
        distribution = sorted(distribution.items(), key=lambda x: x[1])
        try:
            sId = distribution[0][0].staffId
        except:
            return render(request, 'error-404.html', {'msg': '当前没有客服人员！'})
        nrctask = smodels.release_task_check(
            staffId_id=sId,
            subTime=datetime.datetime.now(),
            taskId_id=task.taskId
        )
        try:
            if dType == "pic":
                for i in range(len(pictures)):
                    new_data = cmodels.data(
                        dType=dType,
                        dFile=pictures[i],
                        taskId_id=task.taskId,
                        description=dataDescription,
                        dLink=dLink
                    )
                    new_data.save()
            else:
                new_data = cmodels.data(
                    dType=dType,
                    dFile=fBytes,
                    taskId_id=task.taskId,
                    description=dataDescription,
                    dLink=dLink
                )
                new_data.save()
        except:
            task.delete()
            return render(request, 'error-404.html', {'msg': '数据保存时发生错误！请检查文件中的相关路径！'})
        nrctask.save()
        return redirect(f'/creator/{name}/task_list', {'name': name})


def task_update(request, name):
    '''
    该函数获取前端页面提交的任务创建请求，并根据前端页面提供的内容创建新的任务
    '''
    if request.method == "GET":
        taskId = request.GET.get('taskId')
        task = cmodels.task.objects.get(taskId=taskId)
        delete = request.GET.get('delete')
        if delete:
            task.deleted = 1
            task.save()
            # 同时需要删除正在待发布审核中的内容以及试标注中的相关任务
            rctask = smodels.release_task_check.objects.get(taskId_id=task.taskId)
            rctask.checkResult = 'unpass'
            rctask.feedBack = '任务已被删除'
            rctask.finTime = datetime.datetime.now()
            rctask.save()
        return redirect(f'/creator/{name}/task_list', {'name': name, 'type': '任务发布者', 'task': task})
    elif request.method == "POST":
        # 获取前端提供的任务相关信息
        taskName = request.POST.get('taskName')
        taskContent = request.POST.get('taskContent')
        taskType = request.POST.get('taskType')
        taskLimit = request.POST.get('taskLimit')
        taskReward = request.POST.get('taskReward')
        cId = cmodels.creator.objects.get(name=name).cId
        taskId = request.POST.get('taskId')
        datas = cmodels.data.objects.filter(taskId_id=taskId)
        # 获取前端提供的数据链接，并将新建数据5
        dLink = request.POST.get('dLink')
        if dLink:
            for data in datas:
                data.dLink = dLink
        description = request.POST.get('description')
        if description:
            for data in datas:
                data.description = description
        # 获取前端上传的数据，判断是否进行了修改
        file = request.FILES.get('file')
        if file:
            fBytes = file.read()
            dType = 0
            excels = ['xlsx', 'xls', 'csv']
            with io.BytesIO(fBytes) as f:
                with zipfile.ZipFile(f, 'r') as zfile:
                    fname = zfile.namelist()[0]
                    ftype = fname.split('.')[-1]
                    if ftype in excels:
                        dType = 'word'
                    else:
                        dType = 'pic'
            if dType == "pic":
                pictures = []
                # 将图片存储到数据库中
                with io.BytesIO(fBytes) as f:
                    with zipfile.ZipFile(f, 'r') as zfile:
                        for fname in zfile.namelist():
                            with zfile.open(fname, mode='r') as tfile:
                                img = tfile.read()
                                pictures.append(img)
                for data in datas:
                    data.delete()
                for i in range(len(pictures)):
                    new_data = cmodels.data(
                        dType=dType,
                        dFile=pictures[i],
                        taskId_id=taskId,
                        description=description,
                        dLink=dLink
                    )
                    new_data.save()
            else:
                datas[0].delete()
                new_data = cmodels.data(
                    dType=dType,
                    dFile=fBytes,
                    taskId_id=taskId,
                    description=description,
                    dLink=dLink
                )
                new_data.save()

        task = cmodels.task.objects.get(taskId=taskId)
        task.taskName = taskName
        task.taskContent = taskContent
        task.taskLimit = taskLimit
        task.reward = taskReward
        task.taskType = taskType
        task.lastUpdate = datetime.datetime.now()
        task.save()

        # 判断是否是重新提交审核的任务
        # 重新上传审核任务
        btnType = request.POST.get('action')
        if btnType == "changeAndSubmit" and task.status == 'unpass':
            rctask = smodels.release_task_check.objects.get(taskId_id=taskId)
            task.status = "checking"
            task.save()
            rctask.checkResult = None
            rctask.subTime = datetime.datetime.now()
            rctask.save()
        return redirect(f'/creator/{name}/task_list', {'name': name})

def getTaskInfo(tasks):
    for task in tasks:
        taskId = task.taskId_id
        origin_task = cmodels.task.objects.get(taskId=taskId)
        cName = cmodels.creator.objects.get(cId=origin_task.cId_id).name
        task.taskName = origin_task.taskName
        task.cName = cName
        task.reward = origin_task.reward
        task.taskType = origin_task.get_taskType_display()
        print(task.taskType)
        task.checkfinTime = cmodels.checkTask.objects.get(taskId_id=taskId, checkResult__isnull=False, checkType='labelCheck').finTime
    return tasks

def info(request, name):
    '''
    进入到个人信息页面，查看自己的余额和其他总体情况并修改自己的简介等内容
    '''
    cId = cmodels.creator.objects.get(name=name).cId
    info = cmodels.creator.objects.get(cId=cId)
    jsTasks = getTaskInfo(fmodels.point.objects.filter(cId_id=cId, status="settle"))
    txTasks = fmodels.point.objects.filter(cId_id=cId, status="withdraw")
    jfTasks = list(chain(jsTasks, txTasks))
    rpoint = 0
    for task in jsTasks:
        rpoint += task.trasaction
    for task in jfTasks:
        if task in jsTasks:
            task.type="结算任务"
        else:
            task.type = "提现任务"
    info.rpoint = rpoint
    overTasks = getTaskInfo(fmodels.point.objects.filter(cId_id=cId, status="over"))
    for overTask in overTasks:
        if overTask.pId_id:
            if overTask.pId.cId_id:
                overTask.type = '补偿'
            elif overTask.pId.wId_id:
                overTask.type = '惩罚'
                overTask.trasaction = '-'+str(overTask.trasaction)
        else:
            overTask.trasaction = '-'+str(overTask.trasaction)
    return render(request, 'creator/info.html',
                  {'name':name, 'info':info,
                   'jsTasks':jsTasks,
                   'overTasks':overTasks,
                   'jfTasks':jfTasks,
                   'txTasks':txTasks})

def info_change(request, name):
    '''
    修改个人信息页面，将修改后的信息保存到数据库中
    '''
    cId = cmodels.creator.objects.get(name=name).cId
    info = cmodels.creator.objects.get(cId=cId)
    if request.method == "GET":
        return render(request, "creator/info_change.html", {'name': name, 'info': info})
    elif request.method == "POST":
        skills = request.POST.get('skills')
        # status = request.POST.get('status')
        phone = request.POST.get('phone')
        mail = request.POST.get('mail')
        info.skill = skills
        info.phone = phone
        info.email = mail
        info.save()
        return redirect(f"/creator/{name}/info", {'name': name, 'info': info})


def task_search(request, name):
    cId = cmodels.creator.objects.get(name=name)
    search = request.GET.get('search')
    tasks = cmodels.task.objects.filter(cId_id=cId, taskName__icontains=search)
    return render(request, 'creator/task_list.html', {'name': name, 'tasks': tasks})


def get_page_taskList(taskType, page, cId):
    if taskType == "tasks":
        tasks = cmodels.task.objects.filter(cId=cId, deleted=0)
    if taskType == "labelTasks":
        # 获取标注中任务的所有信息
        labelTasks = cmodels.task.objects.filter(cId=cId, status='labeling')
        # 将任务进度和任务接受者的相关信息添加进去
        for task in labelTasks:
            # 将任务内容的显示长度控制在10个字符
            task.taskContent = task.taskContent[:10] + '...'
            task.wId = wmodels.acceptedTask.objects.get(taskId_id=task.taskId, delete=0, status='labeling').wId_id
            task.wName = wmodels.worker.objects.get(wId=task.wId).name
            task.acceptTime = wmodels.acceptedTask.objects.get(taskId_id=task.taskId, delete=0,
                                                               status='labeling').acceptTime
    if taskType == "checkTasks":
        # 获取当前任务发布者所有待审核任务信息，包括试标注的任务和标注完成的任务
        checkTasks = cmodels.checkTask.objects.filter(cId_id=cId, checkResult=None)
        # 获取任务属性
        for task in checkTasks:
            task.taskName = cmodels.task.objects.get(taskId=task.taskId_id).taskName
            task.taskContent = cmodels.task.objects.get(taskId=task.taskId_id).taskContent[:10] + '...'
            # 试标注审核
            if task.checkType == "labelTryCheck":
                task.worker = wmodels.worker.objects.get(
                    wId=wmodels.labelTry.objects.get(taskId_id=task.taskId_id).wId_id).name
                task.wId_id = wmodels.worker.objects.get(
                    wId=wmodels.labelTry.objects.get(taskId_id=task.taskId_id).wId_id).wId
            # 标注审核
            else:
                print(task.taskId_id)
                task.worker = wmodels.worker.objects.get(
                    wId=wmodels.acceptedTask.objects.get(taskId_id=task.taskId_id, delete=0).wId_id).name
                task.wId_id = wmodels.worker.objects.get(
                    wId=wmodels.acceptedTask.objects.get(taskId_id=task.taskId_id, delete=0).wId_id).wId
    if taskType == "rcTasks":
        # 获取所有待发布任务
        rcTasks = cmodels.task.objects.filter(cId=cId, status='rChecking', deleted=0)
        for task in rcTasks:
            task.taskContent = task.taskContent[:10] + '...'
            rctask = smodels.release_task_check.objects.get(taskId_id=task.taskId)
            task.sId_id = rctask.staffId_id
            task.subTime = rctask.subTime
    if taskType == "problems":
        # 获取所有申诉内容
        problems = smodels.problem.objects.filter(cId_id=cId)
    return eval(taskType)


def task_list(request, name):
    # 获取页码，如果没有默认是1获取任务类型
    pageSize = 5
    page = request.GET.get('page', 1)
    taskType = request.GET.get('taskType', 'tasks')
    print(taskType, page)
    cId = cmodels.creator.objects.get(name=name).cId
    tasksList = get_page_taskList(taskType, page, cId)
    tasksList = Paginator(tasksList, pageSize)
    print(tasksList.page(1))
    try:
        tasksList = tasksList.page(page)
    except:
        tasksList = tasksList.page(1)
    tasks = get_page_taskList('tasks', 1, cId)
    rcTasks = get_page_taskList('rcTasks', 1, cId)
    labelTasks = get_page_taskList('labelTasks', 1, cId)
    checkTasks = get_page_taskList('checkTasks', 1, cId)
    problems = get_page_taskList('problems', 1, cId)
    return render(request, 'creator/task_list.html',
                  {'name': name,
                   'tasksList': tasksList,
                   'tasks': tasks,
                   'rcTasks': rcTasks,
                   'labelTasks': labelTasks,
                   'checkTasks': checkTasks,
                   'problems': problems,
                   'active': taskType})


def other_info(request, name):
    type = request.GET.get('type')
    Id = request.GET.get('Id')
    if type == "worker":
        workerName = wmodels.worker.objects.get(wId=Id).name
        return render(request, 'creator/other_info.html', {'name': name, 'workerName': workerName})
    elif type == "creator":
        creatorName = cmodels.creator.objects.get(cId=Id).name
        return render(request, 'creator/other_info.html', {'name': name, 'workerName': creatorName})


def task_info(request, name):
    taskId = request.GET.get('taskId')
    task = cmodels.task.objects.get(taskId=taskId)
    origin_datas = cmodels.data.objects.filter(taskId_id=task.taskId)
    # 添加审核结果
    rctask = smodels.release_task_check.objects.get(taskId_id=taskId)
    task.checkResult = rctask.checkResult
    if task.checkResult == "unpass":
        task.feedBack = rctask.feedBack
    # Excel文件预览处理
    datas = []
    if origin_datas[0].dType == 'word':
        with io.BytesIO(origin_datas[0].dFile) as f:
            with zipfile.ZipFile(f, 'r') as zfile:
                fname = zfile.namelist()[0]
                with zfile.open(fname, mode='r') as tfile:
                    try:
                        tdata = pd.read_excel(tfile, header=None)
                    except:
                        tdata = pd.read_csv(tfile, header=None, error_bad_lines=False)
        count = 0
        for i in range(tdata.shape[0]):
            if count < 10:
                datas.append(list(tdata.iloc[i, :]))
                count += 1
            else:
                break
    elif origin_datas[0].dType == 'pic':
        '''with io.BytesIO(data.dFile) as f:
            with zipfile.ZipFile(f, 'r') as zfile:
                count = 0
                for fname in zfile.namelist():
                    with zfile.open(fname, mode='r') as tfile:
                        img = tfile.read()
                        image_base4 = base64.b64encode(img).decode('utf8')
                        if count<=10:
                            datas.append(image_base4)
                            count += 1
                        else:
                            break'''
        for i in range(len(origin_datas)):
            datas.append(base64.b64encode(origin_datas[i].dFile).decode('utf8'))
    type = request.GET.get('type')
    # with io.BytesIO(task.taskDescription) as f:
    #     print(f.read())
    # print(task.taskDescription)
    # 添加任务的试标注标注结果
    task.labelTrys = []
    try:
        labelTrys = wmodels.labelTry.objects.filter(taskId_id=taskId)
        for labelTry in labelTrys:
            if labelTry.status == 'checking':
                task.labelTrys.append(labelTry)
    except:
        pass
    try:
        label = wmodels.acceptedTask.objects.get(taskId_id=taskId, delete=0, status='checking')
        task.labelResult = label.result
    except:
        task.labelResult = None
    len_of_project = len(cmodels.data.objects.filter(taskId_id=int(taskId)))
    len_of_label = len(wmodels.labels.objects.filter(taskId_id=int(taskId)))
    task.progress = '{:.2f}%'.format(len_of_label / len_of_project *100)
    return render(request, 'creator/task_info.html',
                  {'task': task, 'name': name, 'origin_datas': origin_datas, 'type': type, 'datas': datas})


def check(request, name):
    if request.method == "POST":
        taskId = request.POST.get('taskId')
        btnAction = request.POST.get('action')
        # if btnAction=="checkResultSubmit":
        # 审核完成，获取审核结果
        checkResult = request.POST.get('checkResult')
        type = request.POST.get('type')
        # 更新审核任务列表中的任务状态和审核结果
        print(type, checkResult)
        # 更新任务列表中的任务状态
        task = cmodels.task.objects.get(taskId=taskId)
        if type == "label":
            ctask = cmodels.checkTask.objects.get(taskId_id=taskId, checkResult__isnull=True, checkType="labelCheck")
            ctask.checkResult = checkResult
            ctask.finTime = datetime.datetime.now()
            # 更新任务接受者接受任务列表中的任务状态
            acceptTask = wmodels.acceptedTask.objects.get(taskId_id=taskId, delete=0, status='checking')
            acceptTask.status = 'over'
            acceptTask.finTime = datetime.datetime.now()
            task.status = 'over'
            try:
                # 积分任务添加
                punishs = fmodels.punish.objects.all()
                points = fmodels.point.objects.all()
                financers = mmodels.staff.objects.filter(staffType='F', staffStatus='A', deleted=0)
                distribution = {}
                for financer in financers:
                    distribution[financer] = len(punishs.filter(staffId_id=financer.staffId)) + len(
                        points.filter(staffId_id=financer.staffId))
                distribution = sorted(distribution.items(), key=lambda x: x[1])
                fId = distribution[0][0].staffId
                point = fmodels.point(
                    cId_id=task.cId_id,
                    wId_id=acceptTask.wId_id,
                    trasaction=task.reward,
                    staffId_id=fId,
                    status='settle',
                    taskId_id=taskId,
                    pDate=datetime.datetime.now()
                )
            except:
                return render(request, 'error-404.html', {'msg':'当前没有财务工作人员！'})
            point.save()
            acceptTask.save()
            ctask.save()
            task.save()
        else:
            ctask = cmodels.checkTask.objects.get(taskId_id=taskId, checkResult=None, checkType="labelTryCheck")
            ctask.checkResult = checkResult
            ctask.finTime = datetime.datetime.now()
            ctask.save()
            tryTask = wmodels.labelTry.objects.get(taskId_id=taskId)
            tryTask.status = 'over'
            tryTask.checkResult = checkResult
            tryTask.save()
            task.status = 'unAccept'
            task.save()
        return redirect(f'/creator/{name}/task_list', {'name': name})


def problem_create(request, name):
    cId = cmodels.creator.objects.get(name=name).cId
    if request.method == "GET":
        tasks = cmodels.task.objects.filter(cId_id=cId)
        return render(request, f"creator/problem_create.html", {'name': name, 'tasks': tasks})
    elif request.method == "POST":
        pContent = request.POST.get("pContent")
        taskId = request.POST.get('taskId')
        type = request.POST.get('type')
        existProblems = smodels.problem.objects.filter(taskId_id=taskId, cId_id=cId)
        if len(existProblems) > 0:
            return render(request, 'error-404.html', {'msg': '已存在当前任务的申诉信息'})
        # 将申诉信息提交到客服
        services = smodels.problem.objects.all()
        servicers = mmodels.staff.objects.filter(staffType='S', staffStatus='A')
        distribution = {}
        for servicer in servicers:
            distribution[servicer] = len(services.filter(staffId_id=servicer.staffId))
        distribution = sorted(distribution.items(), key=lambda x: x[1])
        sId = distribution[0][0].staffId
        sproblem = smodels.problem(
            cId_id=cId,
            # 将任务分配给其中一位职员，优先分配给任务最少的职员
            staffId_id=sId,
            pContent=pContent,
            type=type,
            taskId_id=taskId,
            subTime=datetime.datetime.now(),
            status='unHandle',
        )
        sproblem.save()
        return redirect(f'/creator/{name}/task_list', {'name': name})


def charts(request, name):
    cId = cmodels.creator.objects.get(name=name).cId
    # 数据处理和分析统计
    # 全部任务数量
    taskAll = len(cmodels.task.objects.filter(cId_id=cId))
    # 待发布审核中任务数量
    rcTasks = len(cmodels.task.objects.filter(cId_id=cId, status='rChecking'))
    # 标注中任务数量
    labelTasks = len(cmodels.task.objects.filter(cId_id=cId, status='labeling'))
    # 已完成任务数量
    completeTasks = len(cmodels.task.objects.filter(cId_id=cId, status='over'))
    # 待审核任务数量
    checkTasks = len(cmodels.checkTask.objects.filter(cId_id=cId, checkResult=None))
    # 审核完成任务数量
    checkedTasks = len(cmodels.checkTask.objects.filter(cId_id=cId, checkResult=True))
    # 不同类型任务统计
    tasks = cmodels.task.objects.filter(cId_id=cId)
    typeTasks = {}
    for task in tasks:
        typeTasks[task.get_taskType_display()] = typeTasks.get(task.get_taskType_display(), 0) + 1
    typeTasks = list(typeTasks.items())
    return render(request, 'creator/charts.html',
                  {'name': name,
                   'taskAll': taskAll,
                   'rcTasks': rcTasks,
                   'labelTasks': labelTasks,
                   'completeTasks': completeTasks,
                   'checkTasks': checkTasks,
                   'checkedTasks': checkedTasks,
                   'typeTasks': typeTasks
                   })


def save_json_file(data, filename):
    # 将字典对象保存为 JSON 文件
    with open(filename, 'w') as f:
        json.dump(data, f)


def save_img_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)


def labelResultDownload(request, name, taskId):
    label_result = wmodels.labels.objects.filter(taskId_id=taskId)
    data_result = cmodels.data.objects.filter(taskId_id=taskId)
    for i, label in enumerate(label_result):
        label_json = label.label
        filename = "./data/labels/" + f'label{label.lId}.json'
        save_json_file(label_json, filename)
    for i, data in enumerate(data_result):
        data_img = data.dFile
        filename = "./data/imgs/" + f'data{data.dId}.jpg'
        save_img_file(data_img, filename)
    # 打包多个 JSON 文件成 ZIP 文件
    zip_name="./data/" + name + '-' + str(taskId) + '-data.zip'
    with zipfile.ZipFile(zip_name, 'w') as zip:
        for filename in os.listdir('./data/imgs/'):
            if filename.endswith('.jpg'):
                zip.write("data/imgs/"+filename)
                os.remove("data/imgs/"+filename)
        for filename in os.listdir('./data/labels/'):
            if filename.endswith('.json'):
                zip.write("data/labels/"+filename)
                os.remove("data/labels/"+filename)
    # 构造 ZIP 文件下载的响应
    with open("./data/" + name + '-' + str(taskId) + '-data.zip', 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="data.zip"'

    # 返回文件下载的响应
    return response


# =============================================================================================
# =============================================================================================
# =============================================================================================
# =============================================================================================
# =============================================================================================
from django.http import HttpResponse
from django.shortcuts import render, redirect
import json
from django.views.decorators.csrf import csrf_exempt
import io
import base64


@csrf_exempt
def labelResult(request, name, taskId):
    # 进入任务标注结果查界面
    label_url = "/creator/" + name + "/" + taskId
    if request.method == "GET":
        # taskId_ano = request.GET.get('taskId')
        lenth_of_imgs = len(cmodels.data.objects.filter(taskId_id=int(taskId)))
        lenth_of_labels = len(wmodels.labels.objects.filter(taskId_id=taskId))
        print(lenth_of_labels)
        if lenth_of_labels == 0:
            data = {"lenth": lenth_of_imgs,
                    "index_now": 1,
                    "taskId_ano": taskId,
                    "label_url": label_url,
                    "identity": "creator",
                    }
        else:
            data = {"lenth": lenth_of_imgs,
                    "index_now": lenth_of_labels,
                    "taskId_ano": taskId,
                    "label_url": label_url,
                    "identity": "creator",
                    }
        return render(request, "index_ano.html", {"init_data": data, 'name':name, 'taskId':taskId, 'userType':'creator'})
    elif request.method == "POST":
        print("You are not allowed to change the data!")
    else:
        return HttpResponse()


def getlink(request, name, taskId):
    index = request.GET.get("index")  # 项目中的图片的index，还需要知道图片的真正的index
    # taskid_ano=request.GET.get("taskid_ano")
    obj_lis = cmodels.data.objects.filter(taskId_id=int(taskId))
    # map_dic结构如下：{index:true_index}
    # map_dic={}
    # for temp_index in range(len(obj_lis)):
    #     map_dic[str(temp_index)]=obj_lis[temp_index]["id"]
    obj = obj_lis[int(index) - 1]
    img = obj.dFile
    true_id = obj.dId
    # img = Image.open(io.BytesIO(img))
    # img_array = np.asarray(img)
    # print(img_array.shape)
    # buffer = BytesIO()
    # img.save(buffer, format='PNG')  # 将PIL Image对象转化为PNG格式
    image_b64 = base64.b64encode(img).decode('utf-8')  # 将图片转化为base64编码格式

    len_of_project = len(cmodels.data.objects.filter(taskId_id=int(taskId)))
    len_of_label = len(wmodels.labels.objects.filter(taskId_id=int(taskId)))
    progress = '{:.2f}%'.format(len_of_label / len_of_project *100)

    task = cmodels.task.objects.get(taskId=taskId)
    if len(wmodels.labels.objects.filter(lId=true_id)) != 0:
        print("已经经过标注")
        label = wmodels.labels.objects.get(lId=true_id)
        context = {'project_id': taskId,
                   'true_id': true_id,
                   "progress": progress,
                   "len_of_label": str(len_of_label),
                   "label": label.label,
                   "task_type": str(task.taskType),
                   'image_b64': image_b64}
        json_data = json.dumps(context)

        return HttpResponse(json_data, content_type='application/json')
    else:
        print("未经过标注")
        context = {'project_id': taskId,
                   'true_id': true_id,
                   "progress": progress,
                   "len_of_label": str(len_of_label),
                   "label": False,
                   "task_type": str(task.taskType),
                   'image_b64': image_b64}
        json_data = json.dumps(context)
        return HttpResponse(json_data, content_type='application/json')
