import datetime

from django.db import models
from creator import models as cmodels
from creator.models import task

# Create your models here.
class worker(models.Model):
    wId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    email = models.EmailField()
    phone = models.CharField(max_length=11)
    pwd = models.CharField(max_length=16)
    score = models.FloatField(default=0)
    # tags = models.ManyToManyField(tag)
    point = models.IntegerField(default = 0)

class labels(models.Model):
    lId=models.AutoField(primary_key=True)
    taskId = models.ForeignKey(task, to_field='taskId', on_delete=models.CASCADE, null=True)
    label = models.JSONField()
    description = models.TextField(null=True)

class acceptedTask(models.Model):
    taskId = models.ForeignKey(cmodels.task, to_field="taskId", on_delete=models.CASCADE)
    wId = models.ForeignKey(worker, to_field="wId", on_delete=models.CASCADE)
    acceptTime = models.DateTimeField()
    statuss = (
        ('labeling', '标注中'),
        ('checking', '审核中'),
        ('changing', '修改中'),
        ('over', '已完成')
    )
    status = models.CharField(choices=statuss, max_length=20)
    finTime = models.DateTimeField(default=None, null=True)
    delete = models.BooleanField(default=0)
    result = models.ForeignKey(labels, to_field='lId', on_delete=models.CASCADE, null=True)


class labelTry(models.Model):
    taskId = models.ForeignKey(cmodels.task, to_field="taskId", on_delete=models.CASCADE)
    wId = models.ForeignKey(worker, to_field="wId", on_delete=models.CASCADE)
    labelResult = models.JSONField(null=True)
    results = (
        ('good', '优质'),
        ('pass', '通过'),
        ('low', '低质'),
        ('unpass', '未通过')
    )
    statuss = (
        ('labeling', '标注中'),
        ('checking', '审核中'),
        ('over', '已完成')
    )
    status = models.CharField(choices=statuss, max_length=20)
    checkResult = models.CharField(choices=results, default=None, null=True, max_length=20)
    subTime = models.DateTimeField()
    deleted = models.BooleanField(default=False)

class evaluate(models.Model):
    cId = models.ForeignKey(cmodels.creator, to_field="cId", on_delete=models.CASCADE)
    wId = models.ForeignKey(worker, to_field="wId", on_delete=models.CASCADE)
    score = models.IntegerField()
    eTime = models.DateTimeField()
    taskId = models.ForeignKey(cmodels.task, to_field="taskId", on_delete=models.CASCADE)

class problem(models.Model):
    wpId = models.AutoField(primary_key=True)
    wId = models.ForeignKey(worker, to_field="wId", related_name="problem_wId", on_delete=models.CASCADE, null=True)
    pContent = models.TextField()
    pName = models.CharField(max_length=40, null=True)
    taskId = models.ForeignKey(cmodels.task, to_field="taskId", related_name="wproblem_taskId", on_delete=models.CASCADE, null=True)
    subTime = models.DateTimeField()
    statuss = (
        ('toHandle', '未处理'),
        ('handled', '已处理')
    )
    status = models.CharField(choices=statuss, max_length=20)
    types = (
        ('taskResult', "任务审核结果申诉"),
        ('taskReward', "任务奖励发放申诉"),
        ('account', "个人账户信息申诉"),
        ('labelSystem', "标注系统异常申诉"),
    )
    type = models.CharField(choices=types, null=True, max_length=20)
    feedBack = models.TextField(null=True)
    finTime = models.DateTimeField(null=True)

class comment(models.Model):
    cmId = models.AutoField(primary_key=True)
    cId = models.ForeignKey(cmodels.creator, to_field="cId", related_name="comment_cId", on_delete=models.CASCADE)
    wId = models.ForeignKey(worker, to_field="wId", related_name="comment_wId", on_delete=models.CASCADE)
    taskId = models.ForeignKey(cmodels.task, to_field="taskId", related_name="comment_taskId", on_delete=models.CASCADE)
    content = models.TextField()
    cmTime = models.DateTimeField()
    choice = (
        ('creator', '任务接受者'),
        ('worker', '任务发布者')
    )
    promoter = models.CharField(choices=choice, max_length=20)
