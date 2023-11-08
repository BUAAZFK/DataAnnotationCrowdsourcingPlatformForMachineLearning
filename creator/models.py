import datetime

from django.db import models
# Create your models here.

class creator(models.Model):
    cId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    email = models.EmailField()
    phone = models.CharField(max_length=11)
    pwd = models.CharField(max_length=16)
    point = models.IntegerField(default = 0)

class task(models.Model):
    taskId = models.AutoField(primary_key=True)
    taskName = models.CharField(max_length=200, default=None)
    cover = models.BinaryField(null=True)
    cId = models.ForeignKey(creator, to_field='cId', on_delete=models.CASCADE)
    taskContent = models.TextField()
    taskDescription = models.BinaryField(null=True)
    createTime = models.DateTimeField(null=True)
    types = (
        ('textClean', '文本清洗'),
        ('emotionLable', '情感标注'),
        ('textClass', '文本分类'),
        ('semanticSeg', '语义分割'),
        ('picClass', '图片分类'),
        ('objectDetection', '目标检测')
    )
    taskType = models.CharField(choices=types, max_length=20)
    taskLimit = models.DateTimeField(max_length=20)
    deleted = models.BooleanField(default=False)
    reward = models.CharField(max_length=20, default=0)
    statuss = (
        ('rChecking', '发布审核中'),
        ('unpass', '审核未通过'),
        ('unAccept', '未被接受'),
        ('labeling', '标注中'),
        ('checking', '审核中'),
        ('over', '已完成'),
        ('cancel', '已取消'),
    )
    status = models.CharField(choices=statuss, default='rChecking', max_length=20)
    lastUpdate = models.DateTimeField(default='2023-05-01 00:00:00')

class data(models.Model):
    types = (
        ('word', '文字'),
        ('pic', '图片'),
        ('video', '视频')
    )
    dId = models.AutoField(primary_key=True)
    dLink = models.URLField(max_length=100, null=True)
    dType = models.CharField(choices=types, max_length=20)
    dFile = models.BinaryField(null=True)
    taskId = models.ForeignKey(task, to_field='taskId', on_delete=models.CASCADE, null=True)
    description = models.TextField(null=True)


class checkTask(models.Model):
    checkId = models.AutoField(primary_key=True)
    cId = models.ForeignKey(creator, to_field='cId', on_delete=models.CASCADE)
    taskId = models.ForeignKey(task, to_field="taskId", on_delete=models.CASCADE)
    subTime = models.DateTimeField()
    results = (
        ('good', '优质'),
        ('pass', '通过'),
        ('low', '低质'),
        ('unpass', '未通过')
    )
    checkResult = models.CharField(choices=results, null=True, max_length=20)
    finTime = models.DateTimeField(default=None, null=True)
    type = (
        ('labelTryCheck', '试标注审核'),
        ('labelCheck', '标注审核')
    )
    checkType = models.CharField(choices=type, max_length=20)

class problem(models.Model):
    cpId = models.AutoField(primary_key=True)
    pName = models.CharField(max_length=40, null=True)
    cId = models.ForeignKey(creator, related_name="p_cId", to_field="cId", on_delete=models.CASCADE)
    taskId = models.ForeignKey(task, to_field="taskId", related_name="cproblem_taskId", on_delete=models.CASCADE, null=True)
    pContent = models.TextField()
    subTime = models.DateTimeField()
    types = (
        ('taskResult', "任务审核结果申诉"),
        ('taskReward', "任务奖励发放申诉"),
        ('account', "个人账户信息申诉"),
        ('labelSystem', "标注系统异常申诉"),
    )
    type = models.CharField(choices=types, null=True, max_length=20)
    statuss = (
        ('unHandle', '未处理'),
        ('handled', '已处理')
    )
    status = models.CharField(choices=statuss, max_length=20)
    feedBack = models.TextField(null=True)
    finTime = models.DateTimeField(null=True)


