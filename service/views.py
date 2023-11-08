import base64
import datetime
import io
import zipfile
from itertools import chain

import pandas as pd
from django.shortcuts import render, redirect
from service import models as smodels
from creator import models as cmodels
from finance import models as fmodels
from worker import models as wmodels
from manager import models as mmodels
from django.http import HttpResponse
import json

# Create your views here.
def index(request, sId):
    sId = mmodels.staff.objects.get(staffId=sId).staffId
    problems = smodels.problem.objects.filter(staffId_id = sId)
    return render(request, "service/index.html", {'problems':problems, 'sId':sId})

def task_list(request, sId):
    sId = mmodels.staff.objects.get(staffId=sId).staffId
    problems = smodels.problem.objects.filter(staffId_id = sId, status='unHandle')
    rctasks = smodels.release_task_check.objects.filter(staffId_id=sId, checkResult__isnull=True)
    for rctask in rctasks:
        tmp_task = cmodels.task.objects.get(taskId=rctask.taskId_id)
        rctask.taskName = tmp_task.taskName
        rctask.taskContent = tmp_task.taskContent
        rctask.taskLimit = tmp_task.taskLimit
        rctask.taskType = tmp_task.get_taskType_display()
        rctask.status = tmp_task.get_status_display()
        rctask.type = "rctask"
        rctask.cName = cmodels.creator.objects.get(cId=tmp_task.cId_id).name
    for problem in problems:
        problem.type = "problem"
        try:
            problem.name = cmodels.creator.objects.get(cId=problem.cId_id).name
        except:
            problem.name = wmodels.worker.objects.get(wId=problem.wId_id).name
    taskAll = list(chain(problems, rctasks))
    taskAll = sorted(taskAll, key=lambda x:x.subTime, reverse=True)
    return render(request, "service/task_list.html", {'taskAll':taskAll, 'rctask':rctasks, 'problem':problems, 'sId':sId})

def get_taskInfo(taskId):
    task = cmodels.task.objects.get(taskId=taskId)
    data = cmodels.data.objects.filter(taskId_id=task.taskId)
    # Excel文件预览处理
    datas = []
    if data[0].dType == 'word':
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
            if count < 10:
                datas.append(list(tdata.iloc[i, :]))
                count += 1
            else:
                break
    elif data[0].dType == "pic":
        for temp in data:
            datas.append(base64.b64encode(temp.dFile).decode('utf8'))
    return task, data, datas

def task_info(request, sId):
    taskId = request.GET.get('taskId')
    task, data, datas = get_taskInfo(taskId)
    pId = request.GET.get('pId')
    return redirect(f"/service/{sId}/{pId}/handle", {'task': task, 'sId': sId, 'datas': datas, 'data': data[0]})

def check(request, sId, taskId):
    '''
    进入待发布任务的check页面
    '''
    if request.method=="GET":
        # sId = smodels.staff.objects.get(n).sId
        type = request.GET.get('type')
        task, data, datas = get_taskInfo(taskId)
        return render(request, "service/check.html", {'task':task, 'sId':sId, 'datas':datas, 'data':data[0]})
    elif request.method=="POST":
        taskId = request.POST.get('taskId')
        rctask = smodels.release_task_check.objects.get(taskId_id=taskId)
        task = cmodels.task.objects.get(taskId=taskId)
        # 任务审核结果添加
        check_result = request.POST.get('pass')
        if check_result=="unpass":
            rctask.checkResult = 'unpass'
            feed_back = request.POST.get('feed_back')
            task.status = 'unpass'
            rctask.feedBack = feed_back
        else:
            rctask.checkResult = "pass"
            task.status = 'unAccept'
        task.save()
        rctask.finTime = datetime.datetime.now()
        rctask.save()
        return redirect(f'/service/{sId}/task_list')


def handle(request, sId, pId):
    sId = mmodels.staff.objects.get(staffId=sId).staffId
    if request.method=="GET":
        # sId = smodels.staff.objects.get(n).sId
        type = request.GET.get('type')
        problem = smodels.problem.objects.get(pId=pId)
        task, data, datas = get_taskInfo(problem.taskId_id)
        return render(request, "service/handle.html", {'problem':problem, 'task':task, 'sId':sId, 'datas':datas, 'data':data[0]})
    elif request.method=="POST":
        pId = request.POST.get('pId')
        feedBack = request.POST.get('feedBack')
        # 添加申诉处理结果
        problem = smodels.problem.objects.get(pId=pId)
        problem.status = 'handled'
        problem.feedBack = feedBack
        problem.finTime = datetime.datetime.now()
        problem.save()
        # 添加惩罚或补偿
        punish = request.POST.get('punish')
        # 获取惩罚或补偿金额
        punishSum = request.POST.get('punishSum') if request.POST.get('punishSum') else 0
        # 如果存在积分处罚，则需要添加积分任务
        if punishSum:
            new_pointTask = fmodels.point(
                trasaction=punishSum,
                status='punish' if punish=="punish" else "compensate",
                pDate=datetime.datetime.now(),
                cId_id=cmodels.task.objects.get(taskId=problem.taskId_id, deleted=0).cId_id,
                staffId_id=problem.staffId_id,
                taskId_id=problem.taskId_id,
                wId_id=wmodels.acceptedTask.objects.get(taskId_id=problem.taskId_id, delete=0).wId_id,
                type='punish' if punish=="punish" else "compensate",
                # 与申诉连接起来
                pId_id=problem.pId
            )
            new_pointTask.save()
        # 为财务工作人员提交需要处罚的申诉内容
        # 选择当前工作最少的进行任务添加
        punishs = fmodels.punish.objects.all()
        financers = mmodels.staff.objects.filter(staffType='F', staffStatus='A', deleted=0)
        distribution = {}
        for financer in financers:
            distribution[financer] = len(punishs.filter(staffId_id=financer.staffId))
        distribution = sorted(distribution.items(), key=lambda x:x[1])
        fId = distribution[0][0].staffId
        new_punish = fmodels.punish(
            staffId_id=fId,
            pId_id=pId,
            punishSum=punishSum,
            status="unHandle"
        )
        new_punish.save()
        return redirect(f'/service/{sId}/task_list')


def labelResultView(request, sId, taskId):
    # 进入任务标注结果查界面
    label_url = "/service/" + sId + "/" + taskId
    pId = request.GET.get('pId')
    if request.method == "GET":
        # taskId_ano = request.GET.get('taskId')
        lenth_of_imgs = len(cmodels.data.objects.filter(taskId_id=int(taskId)))
        lenth_of_labels = len(wmodels.labels.objects.filter(taskId_id=taskId))
        print(lenth_of_labels)
        if lenth_of_labels==0:
            data = {"lenth": lenth_of_imgs,
                    "index_now": 1,
                    "taskId_ano":taskId,
                    "label_url":label_url,
                    "identity":"service",
                    }
        else:
            data={"lenth":lenth_of_imgs,
                  "index_now":lenth_of_labels,
                  "taskId_ano":taskId,
                  "label_url": label_url,
                  "identity": "service",
                  }
        return render(request, "index_ano.html", {"init_data": data, 'pId':pId, 'name':sId, 'userType':'service', 'taskId':taskId})
    elif request.method == "POST":
        print("You are not allowed to change the data!")
    else:
        return HttpResponse()


def getlink(request,  sId, taskId):
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
    progress = '{:.2f}%'.format(len_of_label / len_of_project * 100)

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
