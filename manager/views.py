import datetime
import random
import string

from django.shortcuts import render
from django.shortcuts import render, redirect
from manager import models as mmodels
# Create your views here.
def index(request):
    return render(request, 'manager/index.html')


def staff_manage(request):
    staffs = mmodels.staff.objects.filter(deleted=0)
    return render(request, 'manager/staff_manage.html', {'staffs':staffs})

def generate_password(length):
    # 定义包含大小写字母、数字和特殊字符的字符串集合
    characters = string.ascii_letters + string.digits + string.punctuation
    # 生成密码
    password = ''.join(random.choice(characters) for i in range(length))
    return password

def staff_add(request):
    if request.method=="POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        pwd = request.POST.get('pwd')
        staffType = request.POST.get('staffType')
        if not pwd:
            pwd = generate_password(8)
        staff = mmodels.staff(
            name=name,
            email=email,
            phone=phone,
            pwd=pwd,
            staffType=staffType,
            staffStatus='A'
        )
        staff.save()
        return redirect('/manager/staff_manage')

def staff_update(request):
    if request.method=="POST":
        new_name = request.POST.get('new_name')
        new_email = request.POST.get('new_email')
        new_phone = request.POST.get('new_phone')
        new_pwd = request.POST.get('new_pwd')
        new_staffType = request.POST.get('new_staffType')
        new_staffStatus = request.POST.get('new_staffStatus')
        staffId = request.POST.get('staffId')
        print(staffId)
        staff = mmodels.staff.objects.get(staffId=staffId)
        staff.name = new_name
        staff.email = new_email
        staff.phone = new_phone
        staff.pwd = new_pwd
        staff.staffType = new_staffType
        staff.staffStatus = new_staffStatus
        staff.save()
        return redirect('/manager/staff_manage')

def staff_delete(request):
    staffId = request.GET.get('staffId')
    staff = mmodels.staff.objects.get(staffId=staffId)
    staff.deleted = True
    staff.save()
    return redirect('/manager/staff_manage')

def notice(request):
    if request.method=="GET":
        notices = mmodels.notice.objects.filter(deleted=0)
        for notice in notices:
            notice.noticeContent = notice.noticeContent[:10]+"..."
            with open(f"./statics/temp/{notice.noticeName}.pdf",
                      'wb') as file:
                file.write(notice.noticeFile)
            notice.taskDescriptionPath = f"/statics/temp/{notice.noticeName}.pdf"
        return render(request, 'manager/notice.html', {'notices':notices})

    elif request.method=="POST":
        noticeName = request.POST.get('noticeName')
        noticeContent = request.POST.get('noticeContent')
        noticeFile = request.FILES.get('noticeFile')
        noticeFile = noticeFile.read()

        notice = mmodels.notice(
            noticeName=noticeName,
            noticeContent=noticeContent,
            noticeFile=noticeFile,
            noticeDate=datetime.datetime.now()
        )
        notice.save()
        return redirect('/manager/notice')

def notice_update(request):
    nId = request.POST.get('nId')
    noticeName = request.POST.get('noticeName')
    noticeContent = request.POST.get('noticeContent')
    noticeFile = request.FILES.get('noticeFile')
    noticeFile = noticeFile.read()
    notice = mmodels.notice.objects.get(nId=nId)
    notice.Name = noticeName
    notice.noticeContent = noticeContent
    notice.File = noticeFile
    notice.save()
    return redirect('/manager/notice')

def notice_delete(request):
    nId = request.GET.get('nId')
    notice = mmodels.notice.objects.get(nId=nId, deleted=0)
    notice.deleted = True
    notice.save()
    return redirect('/manager/notice')

def user_manage(request):
    return

