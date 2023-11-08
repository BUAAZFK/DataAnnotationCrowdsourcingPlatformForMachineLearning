from django.db import models
from creator import models as cmodels
from worker import models as wmodels
from manager import models as mmodels
# Create your models here.


class problem(models.Model):
    pId = models.AutoField(primary_key=True)
    pName = models.CharField(max_length=40, null=True)
    cId = models.ForeignKey(cmodels.creator, to_field='cId', on_delete=models.CASCADE, null=True)
    wId = models.ForeignKey(wmodels.worker, to_field='wId', on_delete=models.CASCADE, null=True)
    staffId = models.ForeignKey(mmodels.staff, to_field='staffId', on_delete=models.CASCADE)
    taskId = models.ForeignKey(cmodels.task, related_name="staskId", to_field="taskId", on_delete=models.CASCADE, null=True)
    pContent = models.TextField()
    subTime = models.DateTimeField()
    statuss = (
        ('unHandle', '未处理'),
        ('handled', '已处理')
    )
    types = (
        ('taskResult', "任务审核结果申诉"),
        ('taskReward', "任务奖励发放申诉"),
        ('account', "个人账户信息申诉"),
        ('labelSystem', "标注系统异常申诉"),
    )
    type = models.CharField(choices=types, null=True, max_length=20)
    status = models.CharField(choices=statuss, max_length=20)
    feedBack = models.TextField(null=True)
    choice = (
        ('unpunish', '不处罚'),
        ('punish', '处罚'),
        ('compensate', '补偿')
    )
    punish = models.CharField(choices=choice, null=True, max_length=20)
    finTime = models.DateTimeField(null=True)


class release_task_check(models.Model):
    taskId = models.ForeignKey(cmodels.task, to_field='taskId', on_delete=models.CASCADE)
    staffId = models.ForeignKey(mmodels.staff, to_field='staffId', on_delete=models.CASCADE, null=True)
    subTime = models.DateTimeField()
    results = (
        ('pass', '通过'),
        ('unpass', '未通过')
    )
    checkResult = models.CharField(choices=results, null=True, max_length=20)
    feedBack = models.TextField(null=True)
    finTime = models.DateTimeField(null=True)