import base64
import datetime
import io
import zipfile

import pandas as pd
from django.shortcuts import render, redirect
from worker import models as wmodels
from creator import models as cmodels
from finance import models as fmodels
from service import models as smodels
from manager import models as mmodels
# Create your views here.
def index(request, fId):
    return render(request, "finance/index.html", {'fId':fId})

def task_list(request, fId):
    pointTasks = fmodels.point.objects.filter(staffId_id=fId, finTime__isnull=True)
    for pointTask in pointTasks:
        task = cmodels.task.objects.get(taskId=pointTask.taskId_id)
        pointTask.taskName = task.taskName
    punishTasks = fmodels.punish.objects.filter(staffId_id=fId, status="unHandle")
    for punishTask in punishTasks:
        problem = smodels.problem.objects.get(pId=punishTask.pId_id)
        punishTask.pContent = problem.pContent
        punishTask.problemType = problem.get_type_display()
        punishTask.taskId_id = problem.taskId_id
        punishTask.type = fmodels.point.objects.get(pId_id=punishTask.pId_id).type
    print(pointTasks)
    return render(request, 'finance/task_list.html', {'fId':fId, 'pointTasks':pointTasks, 'punishTasks':punishTasks})

def check(request, fId, taskId):
    '''
    进入积分任务的check页面
    '''
    if request.method=="GET":
        # sId = smodels.staff.objects.get(n).sId
        task = cmodels.task.objects.get(taskId=taskId)
        data = cmodels.data.objects.filter(taskId_id=taskId)
        # Excel文件预览处理
        datas = []
        if data[0].dType == "word":
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
        elif data[0].dType=="pic":
            for temp in data:
                datas.append(base64.b64encode(temp.dFile).decode('utf8'))

        len_of_project = len(cmodels.data.objects.filter(taskId_id=int(taskId)))
        len_of_label = len(wmodels.labels.objects.filter(taskId_id=int(taskId)))
        task.progress = '{:.2f}%'.format(len_of_label / len_of_project * 100)
        task.checkResult = cmodels.checkTask.objects.get(taskId_id=taskId).checkResult
        # 获取当前处理任务的类型，奖励发放、惩罚、补偿
        type = request.GET.get('type')
        # 获取当前需要处理的相关申诉
        pId = request.GET.get('pId')
        print(str(pId))
        if str(pId)!='None':
            problem = smodels.problem.objects.get(pId=pId)
        else:
            problem = None
        return render(request, "finance/check.html", {'task':task, 'fId':fId, 'datas':datas, 'data':data[0], 'type':type, 'problem':problem})
    elif request.method=="POST":
        taskId = request.POST.get('taskId')
        check_result = request.POST.get('pass')
        type = request.POST.get('type')
        pId = request.POST.get('pId')
        print(type, pId)
        if type=="point":
            pointTasks = fmodels.point.objects.get(taskId_id=taskId, type="reward")
            pointTasks.status = "over"
            pointTasks.finTime = datetime.datetime.now()
            pointTasks.save()
            if check_result=='pass':
                # 扣除积分
                creator = cmodels.creator.objects.get(cId=pointTasks.cId_id)
                creator.point -= pointTasks.trasaction
                creator.save()
                # 发放积分
                worker = wmodels.worker.objects.get(wId=pointTasks.wId_id)
                worker.point += pointTasks.trasaction
                worker.save()
            return redirect(f'/finance/{fId}/task_list')
        elif type=="punish":
            pId = request.POST.get('pId')
            pointTask = fmodels.point.objects.get(taskId_id=taskId, status="punish", type="punish")
            pointTask.status = 'over'
            pointTask.finTime = datetime.datetime.now()
            # 扣除需要处罚对象的积分
            problemTask = smodels.problem.objects.get(pId=pId)
            if check_result=='pass':
                creator = cmodels.creator.objects.get(cId=pointTask.cId_id)
                worker = wmodels.worker.objects.get(wId=pointTask.wId_id)
                if problemTask.cId_id:
                    worker.point -= pointTask.trasaction
                    worker.save()
                    creator.point += pointTask.trasaction
                    creator.save()
                elif problemTask.wId_id:
                    creator.point -= pointTask.trasaction
                    creator.save()
                    worker.point += pointTask.trasaction
                    worker.save()
            pointTask.save()
            punishTask = fmodels.punish.objects.get(pId_id=pId, status="unHandle")
            punishTask.status = "handle"
            punishTask.save()
            return redirect(f'/finance/{fId}/task_list')
        elif type=="compensate":
            # 获取相关积分任务的信息
            pointTask = fmodels.point.objects.get(pId_id=pId)
            # 补偿申诉人
            problem = smodels.problem.objects.get(pId=pId)
            if check_result=='pass':
                if problem.cId_id:
                    creator = cmodels.creator.objects.get(cId=problem.cId_id)
                    creator.point += pointTask.trasaction
                    creator.save()
                elif problem.wId_id:
                    worker = wmodels.worker.objects.get(wId=problem.wId_id)
                    worker.point += pointTask.trasaction
                    worker.save()
            pointTask.status = "over"
            pointTask.finTime = datetime.datetime.now()
            pointTask.save()
            punishTask = fmodels.punish.objects.get(pId_id=pId, status="unHandle")
            punishTask.status = "handle"
            punishTask.save()
        return redirect(f'/finance/{fId}/task_list')