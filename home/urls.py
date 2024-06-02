from django.contrib import admin
from django.urls import path 
from home import views

urlpatterns = [
    path('',views.index,name='home'),
    path('professor',views.proflogin,name='plogin'),  
    path('student',views.stulogin,name='slogin'), 
    path('student/shome/viewcourse/<str:username>',views.vcourse,name='viewcourse'), 
    # path('student/shome/credit/<str:username>',views.credittransfer,name='viewcourse'), 
    path('professor/phome/excel',views.uploadxl,name='uploadxl'),
    path('professor/phome/report',views.getreport,name='report'), 
    path('professor/phome/professor/tot_stu_sem_wise',views.get_total_students_per_semester,name='gettotalbysem'), 
    path('professor/phome/professor/stu_sem',views.total_students_in_semester,name='totalstusem'), 
    path('professor/phome/professor/stu_year',views.total_students_in_year,name='totalstuyear'), 
    path('professor/phome/professor/sub',views.sub_report,name='subreport'), 
    path('professor/phome/professor/topper',views.topper_list,name='topperlist'), 
    
    
]
# urls.py in your Django app


