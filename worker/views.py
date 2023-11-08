import base64
import datetime
import io
import zipfile
from itertools import chain

import pandas as pd
from django.shortcuts import render, redirect
from creator import models as cmodels
from worker import models as wmodels
from service import models as smodels
from finance import models as fmodels
from manager import models as mmodels
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def index(request, name):
    '''
    tasks = wmodels.AcceptedTask.objects.all()
    print(tasks)
    for task in tasks:
        ttask = cmodels.Task.objects.get(TaskID=task.TaskID_id)
        task.CId = ttask.CreatorID_id
        ctmp = cmodels.Creator.objects.get(CreatorID=ttask.CreatorID_id).Name
        task.CName = ctmp
        task.TaskName = ttask.TaskName
        task.CreateTime = ttask.CreateTime
        task.Limit = ttask.TaskLimit
        task.Type = ttask.get_TaskType_display()
    '''
    tasks = cmodels.task.objects.filter(status=2)
    return render(request, "worker/index.html", {'name':name, 'tasks':tasks})

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
    wId = wmodels.worker.objects.get(name=name).wId
    info = wmodels.worker.objects.get(name=name)
    jsTasks = getTaskInfo(fmodels.point.objects.filter(wId_id=wId, status="settle"))
    txTasks = fmodels.point.objects.filter(wId_id=wId, status="withdraw")
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
    overTasks = getTaskInfo(fmodels.point.objects.filter(wId_id=wId, status="over"))
    for overTask in overTasks:
        if overTask.pId_id:
            if overTask.pId.wId_id:
                overTask.type = '补偿'
            elif overTask.pId.cId_id:
                overTask.type = '惩罚'
                overTask.trasaction = '-'+str(overTask.trasaction)
    return render(request, 'worker/info.html',
                  {'name':name, 'info':info,
                   'jsTasks':jsTasks,
                   'overTasks':overTasks,
                   'jfTasks':jfTasks,
                   'txTasks':txTasks})


def labelTry(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    taskId = request.GET.get('taskId')
    # 更新任务状态
    task = cmodels.task.objects.get(taskId=taskId)
    task.status="unAccept"
    task.save()

    # 添加试标注任务
    # 首先判断是否存在已有的试标注任务，如果有，先删除再添加
    try:
        tryTask = wmodels.labelTry.objects.get(taskId_id=taskId)
        tryTask.delete()
    except:
        tryTask = wmodels.labelTry(
            taskId_id=taskId,
            status = "labeling",
            deleted=0,
            wId_id=wId,
            subTime=datetime.datetime.now()
        )
        tryTask.save()
    return render(request, 'worker/labelTry.html', {'name':name, 'task':task})

def task_accept(request, name):
    taskId = request.GET.get('taskId')
    # 更新任务状态
    task = cmodels.task.objects.get(taskId=taskId)
    task.status="labeling"
    task.save()
    # 添加新接受任务
    wId = wmodels.worker.objects.get(name=name).wId
    acpTask = wmodels.acceptedTask(
        acceptTime=datetime.datetime.now(),
        status='labeling',
        finTime=None,
        taskId_id=task.taskId,
        wId_id=wId
    )
    acpTask.save()
    # 如果存在试标注任务，则更新试标注任务状态
    try:
        tryTask = wmodels.labelTry.objects.get(taskId_id=taskId, wId_id=wId)
        tryTask.status = "over"
    except:
        pass
    return redirect(f'/worker/{name}/label?taskId={taskId}')

def get_tasksInfo(tasks):
    for task in tasks:
        tmp = cmodels.task.objects.get(taskId=task.taskId_id)
        creator = cmodels.creator.objects.get(cId=tmp.cId_id)
        try:
            task.cId = creator.cId
        except:
            task.cId_id = creator.cId
        task.cName = creator.name
        task.taskContent = tmp.taskContent
        task.taskType = tmp.get_taskType_display
        task.taskLimit = tmp.taskLimit
        task.reward = tmp.reward
        task.taskName = tmp.taskName
        task.createTime = tmp.createTime
        try:
            task.finTime = cmodels.checkTask.objects.get(taskId_id=task.taskId_id).finTime
            task.checkResult = cmodels.checkTask.objects.get(taskId_id=task.taskId_id).checkResult
        except:
            pass
        # 如果任务已经被接受，就不能再接受任务了
        tmp = wmodels.acceptedTask.objects.filter(taskId_id=task.taskId_id, status='labeling')
        if len(tmp)==0:
            task.flag = 0
        else:
            task.flag = 1
    return tasks

def task_list(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    tasks = wmodels.acceptedTask.objects.filter(wId_id=wId, delete=0)
    tasks = get_tasksInfo(tasks)
    tryTasks = wmodels.labelTry.objects.filter(wId_id=wId)
    tryTasks = get_tasksInfo(tryTasks)
    checkTasks = wmodels.acceptedTask.objects.filter(wId_id=wId, status='checking')
    checkTasks = get_tasksInfo(checkTasks)
    labelTasks = wmodels.acceptedTask.objects.filter(wId_id=wId, status='labeling', delete=0)
    labelTasks = get_tasksInfo(labelTasks)
    overTasks = wmodels.acceptedTask.objects.filter(wId_id=wId, status='over')
    overTasks = get_tasksInfo(overTasks)
    problems = smodels.problem.objects.filter(wId_id=wId)
    return render(request, 'worker/task_list.html',
                  {'name':name,
                   'tasks':tasks,
                   'tryTasks':tryTasks,
                   'checkTasks':checkTasks,
                   'labelTasks':labelTasks,
                   'overTasks':overTasks,
                   'problems':problems})

def problem_create(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    if request.method=="GET":
        acceptTasks = wmodels.acceptedTask.objects.filter(wId_id=wId, delete=0)
        acceptTasks = get_tasksInfo(acceptTasks)
        return render(request, f"worker/problem_create.html", {'name':name, 'acceptTasks':acceptTasks})
    elif request.method=="POST":
        pContent = request.POST.get("pContent")
        taskId = request.POST.get('taskId')
        type = request.POST.get('type')
        existProblems = smodels.problem.objects.filter(taskId_id=taskId, wId_id=wId)
        if len(existProblems)>0:
            return render(request, 'error-404.html', {'msg':'已存在当前任务的申诉信息'})
        # 将申诉信息提交到客服
        services = smodels.problem.objects.all()
        servicers = mmodels.staff.objects.filter(staffType='S', staffStatus='A')
        distribution = {}
        for servicer in servicers:
            distribution[servicer] = len(services.filter(staffId_id=servicer.staffId))
        distribution = sorted(distribution.items(), key=lambda x:x[1])
        sId = distribution[0][0].staffId
        sproblem = smodels.problem(
            wId_id=wId,
            # 将任务分配给其中一位职员，优先分配给任务最少的职员
            staffId_id=sId,
            pContent=pContent,
            type=type,
            taskId_id=taskId,
            subTime=datetime.datetime.now(),
            status='unHandle',
        )
        sproblem.save()
        return redirect(f'/worker/{name}/task_list', {'name':name})

def task_submit(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    if request.method=="GET":
        # 获取任务标注结果
        taskId = request.GET.get('taskId')
        # 任务状态修改
        task = cmodels.task.objects.get(taskId=taskId)
        task.status = "checking"
        task.save()
        # 接受者任务状态修改
        acceptTask = wmodels.acceptedTask.objects.get(taskId_id=taskId, wId_id=wId, delete=0)
        acceptTask.status = "checking"
        acceptTask.save()
        # 待审核任务添加
        checkTask = cmodels.checkTask(
            subTime=datetime.datetime.now(),
            checkResult=None,
            finTime=None,
            cId_id=task.cId_id,
            taskId_id=task.taskId,
            checkType="labelCheck"
        )
        checkTask.save()

        return redirect(f'/worker/{name}/task_list')
    # 试标注任务不能中途退出，通过POST的方式提交表单结果
    if request.method=="POST":
        type = request.POST.get('type')
        taskId = request.POST.get('taskId')
        print(type, taskId)
        # if type==""
        # 更新任务列表中的状态
        task = cmodels.task.objects.get(taskId=taskId)
        if type=="labelTry":
            checkType = "labelTryCheck" # 试标注类型的任务
            # 更新试标注任务列表中的状态
            tryTask = wmodels.labelTry.objects.get(taskId_id=taskId)
            tryTask.status = "checking"
            tryTask.labelResult = wmodels.labels.objects.get(taskId_id=tryTask.taskId_id)
            tryTask.save()
        else:
            task.status = "checking" # 审核中
            checkType = "labelCheck" # 正常类型的任务
            # 更新Accept, 添加标注结果
            acpTask = wmodels.acceptedTask.objects.get(taskId_id=taskId, wId_id=wId, delete=0)
            acpTask.status = "checking"
            acpTask.result = wmodels.labels.objects.get(taskId_id=acpTask.taskId_id)
            acpTask.save()
        task.save()
        # 待审核任务添加
        checkTask = cmodels.checkTask(
            subTime=datetime.datetime.now(),
            checkResult=None,
            finTime=None,
            cId_id=task.cId_id,
            taskId_id=task.taskId,
            checkType=checkType
        )
        checkTask.save()

        return redirect(f'/worker/{name}/task_list')

def task_abandon(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    taskId = request.GET.get('taskId')
    print(taskId)
    # 修改任务状态为未被接受
    task = cmodels.task.objects.get(taskId=taskId)
    task.status = "unAccept"
    task.save()
    # 删除已接受任务
    acceptTask = wmodels.acceptedTask.objects.get(taskId_id=taskId, wId_id=wId, delete=0)
    acceptTask.delete = 1
    acceptTask.save()
    return redirect('/', {'name':name})

def task_info(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    taskId = request.GET.get('taskId')
    task = cmodels.task.objects.get(taskId=taskId)
    try:
        acceptTask = wmodels.acceptedTask.objects.get(taskId_id=taskId, wId_id=wId, status='labeling', delete=0)
        task.acceptTime = acceptTask.acceptTime
        task.accepted = 1
    except:
        task.accepted = 0
    data = cmodels.data.objects.filter(taskId_id=taskId)
    # Excel文件预览处理
    datas = []
    if data[0].dType=="word":
        with io.BytesIO(data[0].dFile) as f:
            with zipfile.ZipFile(f, 'r') as zfile:
                fname = zfile.namelist()[0]
                print(fname)
                with zfile.open(fname, mode='r') as tfile:
                    try:
                        tdata = pd.read_excel(tfile, header=None)
                    except:
                        tdata = pd.read_csv(tfile, header=None, error_bad_lines=False)
        count = 0
        for i in range(tdata.shape[0]):
            if count<10:
                datas.append(list(tdata.iloc[i, :]))
                count += 1
            else:
                break
    elif data[0].dType=="pic":
        for temp in data:
            datas.append(base64.b64encode(temp.dFile).decode('utf8'))
    len_of_project = len(cmodels.data.objects.filter(taskId_id=int(taskId)))
    len_of_label = len(wmodels.labels.objects.filter(taskId_id=int(taskId)))
    task.progress = '{:.2f}%'.format(len_of_label / len_of_project *100)
    return render(request, 'worker/task_info.html', {'task':task, 'name':name, 'data':data[0], 'datas':datas})

def other_info(request, name):
    type = request.GET.get('type')
    Id = request.GET.get('Id')
    if type=="worker":
        worker = wmodels.worker.objects.get(wId=Id)
        return render(request, 'worker/other_info.html', {'name':name, 'user':worker})
    elif type=="creator":
        creator = cmodels.creator.objects.get(cId=Id)
        return render(request, 'worker/other_info.html', {'name':name, 'user':creator})

def charts(request, name):
    wId = wmodels.worker.objects.get(name=name).wId
    # 数据处理和分析统计
    # 全部任务数量
    taskAll = len(wmodels.acceptedTask.objects.filter(wId_id=wId, delete=0))
    # 试标注
    tryTasks = len(wmodels.labelTry.objects.filter(wId_id=wId))
    untryTasks = len(wmodels.labelTry.objects.filter(wId_id=wId, checkResult=None))
    # 待审核
    checkTasks = len(wmodels.acceptedTask.objects.filter(wId_id=wId, status='checking'))
    # 标注中
    labelTasks = len(wmodels.acceptedTask.objects.filter(wId_id=wId, status='labeling', delete=0))
    # 已完成任务数量
    completeTasks = len(wmodels.acceptedTask.objects.filter(wId_id=wId, delete=0, status='changing'))
    # 不同类型任务统计
    tasks = wmodels.acceptedTask.objects.filter(wId_id=wId, delete=0)
    tasks = get_tasksInfo(tasks)
    typeTasks = {}
    for task in tasks:
        typeTasks[task.taskType] = typeTasks.get(task.taskType, 0) + 1
    typeTasks = list(typeTasks.items())
    return render(request, 'worker/charts.html',
                  {'name':name,
                   'taskAll':taskAll,
                   'tryTasks':tryTasks,
                   'labelTasks':labelTasks,
                   'completeTasks':completeTasks,
                   'checkTasks':checkTasks,
                   'typeTasks':typeTasks,
                   'untyrTasks':untryTasks,
    })


# =======================================================================================================
# =======================================================================================================
# =======================================================================================================
# =======================================================================================================

from django.http import HttpResponse
from django.shortcuts import render,redirect
import json
from django.views.decorators.csrf import csrf_exempt
import io
import base64
#
# def getprogress(request):
#     len_of_project=len(cmodels.data.objects.filter(taskId_id=int(taskid)))
#     len_of_label=len(wmodels.labels.objects.filter(lId=taskid))
#     progress=len_of_label/len_of_project
#
#     data = {"progress": str(progress),
#             "len_of_label": str(len_of_label)}
#     json_data = json.dumps(data)
#
#     return HttpResponse(json_data,content_type='application/json')


# 本地访问
# def getlink(request):
#     index = request.GET.get("index")
#     return HttpResponse(img_links[int(index)-1])


def getlink(request,name):
    index = request.GET.get("index") # 项目中的图片的index，还需要知道图片的真正的index
    taskid_ano=request.GET.get("taskid_ano")
    obj_lis = cmodels.data.objects.filter(taskId_id=int(taskid_ano))
    # map_dic结构如下：{index:true_index}
    # map_dic={}
    # for temp_index in range(len(obj_lis)):
    #     map_dic[str(temp_index)]=obj_lis[temp_index]["id"]
    obj = obj_lis[int(index)-1]
    img = obj.dFile
    true_id = obj.dId
    # img = Image.open(io.BytesIO(img))
    # img_array = np.asarray(img)
    # print(img_array.shape)
    # buffer = BytesIO()
    # img.save(buffer, format='PNG')  # 将PIL Image对象转化为PNG格式
    image_b64 = base64.b64encode(img).decode('utf-8')  # 将图片转化为base64编码格式

    len_of_project = len(cmodels.data.objects.filter(taskId_id=int(taskid_ano)))
    len_of_label = len(wmodels.labels.objects.filter(taskId_id=int(taskid_ano)))
    progress = '{:.2f}%'.format(len_of_label / len_of_project *100)
    task=cmodels.task.objects.get(taskId=taskid_ano)
    if len(wmodels.labels.objects.filter(lId=true_id))!=0:
        print("已经经过标注")
        label = wmodels.labels.objects.get(lId=true_id)
        context = {'project_id':taskid_ano,
                   'true_id': true_id,
                   "progress": progress,
                   "len_of_label": str(len_of_label),
                   "label":label.label,
                   "task_type":str(task.taskType),
                   'image_b64': image_b64}
        json_data = json.dumps(context)

        return HttpResponse(json_data,content_type='application/json')
    else:
        print("未经过标注")
        context = {'project_id': taskid_ano,
                   'true_id': true_id,
                   "progress": progress,
                   "len_of_label": str(len_of_label),
                   "label": False,
                   "task_type":str(task.taskType),
                   'image_b64': image_b64}
        json_data = json.dumps(context)
        return HttpResponse(json_data, content_type='application/json')

# def label(request, name):
#     wId = wmodels.worker.objects.get(name=name).wId
#     taskId = request.GET.get('taskId')
#     task = wmodels.acceptedTask.objects.get(wId_id=wId, status='labeling', delete=0, taskId_id=taskId)
#     tmp = cmodels.task.objects.get(taskId=task.taskId_id)
#     cname = cmodels.creator.objects.get(cId=tmp.cId_id).name
#     task.cName = cname
#     task.taskContent = tmp.taskContent[:10]+'...'
#     task.taskType = tmp.get_taskType_display
#     task.taskLimit = tmp.taskLimit
#     task.reward = tmp.reward
#     task.taskName = tmp.taskName
#     return render(request, 'worker/label.html', {'name':name, 'task':task})

@csrf_exempt
def label(request,name):
    wId = wmodels.worker.objects.get(name=name).wId
    label_url = "/worker/"+name
    if request.method == "GET":
        taskId_ano = request.GET.get('taskId')
        lenth_of_imgs = len(cmodels.data.objects.filter(taskId_id=int(taskId_ano)))
        lenth_of_labels = len(wmodels.labels.objects.filter(taskId_id=taskId_ano))
        print(lenth_of_labels)
        if lenth_of_labels==0:
            data = {"lenth": lenth_of_imgs,
                    "index_now": 1,
                    "taskId_ano":taskId_ano,
                    "label_url":label_url,
                    "identity": "worker",
                    }
        else:
            data={"lenth":lenth_of_imgs,
                  "index_now":lenth_of_labels,
                  "taskId_ano":taskId_ano,
                  "label_url": label_url,
                  "identity": "worker",
                  }
        return render(request, "index_ano.html", {"init_data": data, 'name':name, 'taskId':taskId_ano, 'userType':'worker'})
    # print(request.GET)
    elif request.method == "POST":
        print("post")
        print(request.POST)
        if request.POST.get('classdata'):
            print("图像分类")
            label_dic=dict(request.POST)
            true_id=int(label_dic['iid'][0])
            project_id=int(label_dic['pid'][0])
            stored_data=label_dic['classdata'][0]
            stored_data = '&'.join([x.split('=')[0] for x in stored_data.split('&')])
            print(stored_data)
            if len(wmodels.labels.objects.filter(lId=true_id)) != 0:
                wmodels.labels.objects.filter(lId=true_id).update(label=stored_data)
            else:
                wmodels.labels.objects.create(lId=int(true_id),taskId_id=int(project_id),label=stored_data)
        else:
            print("分割和检测")
            data_raw = json.loads(request.body.decode())
            print(data_raw)
            true_id=data_raw[-1]['true_id']
            project_id=data_raw[-1]['project_id']
            stored_data=data_raw[:-1]
            if len(wmodels.labels.objects.filter(lId=true_id)) != 0:
                wmodels.labels.objects.filter(lId=true_id).update(label=stored_data)
            else:
                wmodels.labels.objects.create(lId=int(true_id),taskId_id=int(project_id),label=stored_data)
        # return render(request, "index_ano.html",{"init_data":data})
        return HttpResponse()
    else:
        # return render(request, "index_ano.html",{"init_data":data})
        return HttpResponse()