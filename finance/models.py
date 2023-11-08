from django.db import models
from service import models as smodels
from creator import models as cmodels
from worker import models as wmodels
from manager import models as mmodels
# Create your models here.

class point(models.Model):
    cId = models.ForeignKey(cmodels.creator, to_field="cId", related_name="point_cId", on_delete=models.CASCADE)
    wId = models.ForeignKey(wmodels.worker, to_field="wId", related_name="point_wId", on_delete=models.CASCADE)
    trasaction = models.IntegerField()
    taskId = models.ForeignKey(cmodels.task, to_field="taskId", related_name="point_taskId", on_delete=models.CASCADE)
    staffId = models.ForeignKey(mmodels.staff, to_field="staffId", on_delete=models.CASCADE, null=True)
    statuss = (
        ('settle', '结算中'),
        ('withdraw', '提现中'),
        ('punish', '处罚中'),
        ('compensate', '补偿'),
        ('over', '已完成')
    )
    status = models.CharField(choices=statuss, default=1, max_length=20)
    types = (
        ('reward', '任务奖励'),
        ('fill', '充值'),
        ('punish', '惩罚'),
        ('compensate', '补偿')
    )
    type = models.CharField(choices=types, default='reward', max_length=20)
    pDate = models.DateTimeField(null=True)
    # 相关申诉任务，如果是惩罚或补偿的话
    pId = models.ForeignKey(smodels.problem, to_field="pId", on_delete=models.CASCADE, null=True)
    finTime = models.DateTimeField(null=True)
    results = (
        ('pass', '通过'),
        ('unpass', '未通过')
    )
    result = models.CharField(choices=results, max_length=20, default='pass')

class punish(models.Model):
    staffId = models.ForeignKey(mmodels.staff, to_field="staffId", on_delete=models.CASCADE)
    pId = models.ForeignKey(smodels.problem, to_field="pId", related_name="punish_pId", on_delete=models.CASCADE)
    punishSum = models.IntegerField()
    statuss = (
        ('unHandle', '未处理'),
        ('handled', '已处理')
    )
    status = models.CharField(choices=statuss, max_length=20)