from django.shortcuts import render, HttpResponse, redirect
from django.db import connection
from pyexpat.errors import messages

# Create your views here
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages


from django.conf import settings
from django.core.files.storage import FileSystemStorage
import pandas as pd


# Create your views here.
def create_tables():
    with connection.cursor() as cursor:
        # Define SQL queries for creating tables 
        print(settings.MEDIA_ROOT)
        create_studentlogin_table_query = """
            CREATE TABLE IF NOT EXISTS studentlogin (
                sid INT  PRIMARY KEY,
                susername VARCHAR(255),
                spassword VARCHAR(255)
            );
        """

        create_professorlogin_table_query = """
            CREATE TABLE IF NOT EXISTS professorlogin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pusername VARCHAR(255),
                ppassword VARCHAR(255)
            );
        """

        create_student_table_query = """
            CREATE TABLE IF NOT EXISTS student (
                regno INT PRIMARY KEY,
                sname VARCHAR(255),
                FOREIGN KEY (regno) REFERENCES studentlogin(sid) 

            );
        """

        create_course_table_query = """
            CREATE TABLE IF NOT EXISTS course (
               cid VARCHAR(10) PRIMARY KEY, 
               title VARCHAR(100), 
               maxcredits INT
            );
        """
        print("hi")

        create_studied_table_query = """
            CREATE TABLE IF NOT EXISTS studied (
                regno INT,
                cid VARCHAR(10),
                credit_ear INT, 
                act_marks INT, 
                ssn_marks INT, 
                yearofstudy varchar(50), 
                sem int,

                FOREIGN KEY (regno) REFERENCES student(regno),
                FOREIGN KEY (cid) REFERENCES course(cid),
                PRIMARY KEY (regno, cid)
            );
        """

        # Execute the queries
        cursor.execute(create_studentlogin_table_query)
        cursor.execute(create_professorlogin_table_query)
        cursor.execute(create_student_table_query)
        cursor.execute(create_course_table_query)
        cursor.execute(create_studied_table_query)


# Call the function to create tables
create_tables()


# Create your views here.
def index(request):
    # return HttpResponse('this is homepage')
    return render(request, "index.html")


def proflogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        raw_sql_query = """
            SELECT * 
            FROM professorlogin 
            WHERE pusername = %s AND ppassword = %s
        """

        params = [username, password]

        with connection.cursor() as cursor:
            cursor.execute(raw_sql_query, params)
            obj = cursor.fetchone()

        if obj:
            return render(request, "profhome.html")
    return render(request, "proflogin.html")


def stulogin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        raw_sql_query = """
            SELECT * 
            FROM studentlogin 
            WHERE susername = %s AND spassword = %s
        """

        params = [username, password]

        with connection.cursor() as cursor:
            cursor.execute(raw_sql_query, params)
            obj = cursor.fetchone()

        if obj:
            return render(request, "stuhome.html",{'username':username})
    return render(request, "stulogin.html")


def vcourse(request,username):
    # Retrieve the username parameter from the URL
    

    if username:
        # Do something with the username, e.g., fetch user-related data
        # For example, passing the username to a context dictionary to render in a template 
        with connection.cursor() as cursor:
            query = """
            SELECT course.cid,course.title,studied.ssn_marks,studied.yearofstudy,studied.sem
            FROM course
            INNER JOIN studied ON course.cid = studied.cid
            INNER JOIN student ON student.regno = studied.regno 
            inner join studentlogin on studentlogin.sid=student.regno
            WHERE studentlogin.susername = %s
             """
            cursor.execute(query, [username])
            course_details = cursor.fetchall()
    
        return render(request, 'course_details.html', {'course_details': course_details})
        
    else: 
        return HttpResponse("No username provided in the URL.") 
    

def credittransfer(request,username): 
    pass


def uploadxl(request):
    return render(request, "uploadxl.html")


# myapp/views.py


def uploadxl(request):
    if request.method == "POST" and request.FILES["myfile"]:
        myfile = request.FILES["myfile"]
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)

        # Parse the Excel file and save its content to the database
        excel_data = pd.read_excel(settings.MEDIA_ROOT + "/" + filename) 
        

        with connection.cursor() as cursor:
            for index, row in excel_data.iterrows():
                cursor.execute("SELECT susername FROM studentlogin WHERE sid = %s",
                    [row["Register Number"]]) 
                existing_row = cursor.fetchone() 
                if existing_row:
                
                    cursor.execute(
                        "SELECT regno FROM student WHERE regno = %s",
                        [row["Register Number"]],
                    )
                    existing_row = cursor.fetchone()

                    if not existing_row:
                        cursor.execute(
                            "INSERT INTO student VALUES (%s, %s)",
                            [row["Register Number"], row["Student Name"]],
                        )

                    cursor.execute(
                        "SELECT cid FROM course WHERE cid = %s", [row["Sub.Code"]]
                    )

                    existing_row = cursor.fetchone()

                    if not existing_row:
                        cursor.execute(
                            "INSERT INTO course (cid, title) VALUES (%s, %s)",
                            [row["Sub.Code"], row["NPTEL Course Title"]],
                        )

                    cursor.execute(
                        "SELECT regno,cid FROM studied WHERE regno=%s and cid = %s ",
                        [row["Register Number"], row["Sub.Code"]],
                    )

                    existing_row = cursor.fetchone()

                    if not existing_row:
                        cursor.execute(
                            "INSERT INTO studied VALUES (%s, %s,%s,%s,%s,%s,%s)",
                            [
                                row["Register Number"],
                                row["Sub.Code"],
                                row["No of credits earned"],
                                row["Actual NPTEL Marks"],
                                row["SSN Marks (Max 100)"], 
                                row["Year"],
                                row["SEM"]
                            ],
                        )

            
                else:
                    return HttpResponse(f'student {row["Register Number"]} detail entered  doesnt have login id') 
            else:
                return render(
                        request, "uploadxl.html", {"uploaded_file_url": uploaded_file_url}
                    ) 
    return render(request, "uploadxl.html")

def getreport(request):
    return render(request, "getreport.html") 
def get_total_students_per_semester(request):
        try:
            with connection.cursor() as cursor:
                # Execute a raw SQL query to get total students per semester
                cursor.execute(
                    '''
                    SELECT st.sem, COUNT(DISTINCT st.regno) as total_students
                    FROM student s
                    INNER JOIN studied st ON s.regno = st.regno
                    INNER JOIN course c ON st.cid = c.cid
                    GROUP BY st.sem
                    ORDER BY st.sem
                    '''
                )
                # Fetch all the results
                rows = cursor.fetchall()  
                print(rows)


                # Constructing a dictionary with semester as key and total students as value
                result = {row[0]: row[1] for row in rows}  
                print(result)

                
                return render(request,'tot_stu_semwise.html',{'result':result})
        except Exception as e:
            # Handle exceptions, such as database errors or validation issues
            print(f"Error: {e}")
            return {} 
        



def sub_report(request): 
    if request.method == 'GET':
        subject_name = request.GET.get('subject_name', '')

        if subject_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT student.regno as register_number,student.sname AS student_name, course.title AS course_name, studied.ssn_marks,studied.yearofstudy as year
                    FROM student
                    INNER JOIN studied ON student.regno = studied.regno
                    INNER JOIN course ON studied.cid = course.cid
                    WHERE course.title = %s order by studied.yearofstudy
                    """,
                    [subject_name]
                )
                student_data = cursor.fetchall()   
                nstudents=len(student_data)
                
        else:
            student_data = None 
            nstudents=0

        return render(request, 'subject_data.html', {'student_data': student_data ,'nstudents':nstudents,'show_message': request.method == 'POST' and not student_data})
    return render(request, 'subject_data.html') 


def total_students_in_semester(request):
    if request.method == 'GET':
        semester_name = request.GET.get('semester_name', '')

        if semester_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT student.regno as register_number,student.sname AS student_name, course.title AS course_name ,studied.ssn_marks as marks
                    FROM student
                    INNER JOIN studied ON student.regno = studied.regno
                    INNER JOIN course ON studied.cid = course.cid
                    WHERE studied.sem = %s order by student.regno
                    """,
                    [semester_name]
                )
                student_data = cursor.fetchall()  
                cursor.execute(
                    """
                    SELECT count(distinct(student.regno)) as register_number from student inner join studied on student.regno=studied.regno 
                    where studied.sem = %s 
                    """,[semester_name]
                ) 
                nstudents=cursor.fetchone()
                
        else:
            student_data = None 
            nstudents=0

        return render(request, 'tot_stu_in_a_sem.html', {'student_data': student_data ,'nstudents':nstudents,'show_message': request.method == 'POST' and not student_data})
    return render(request, 'tot_stu_in_a_sem.html')


def total_students_in_year(request):
    if request.method == 'GET':
        year_name = request.GET.get('year_name', '')  
        d={'1':'I year','2':'II year','3':'III year','4':'IV year'}
        if year_name in d: 
            year_name=d[year_name] 
        else:
            pass 

        if year_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT student.regno as register_number,student.sname AS student_name, course.title AS course_name ,studied.ssn_marks as marks
                    FROM student
                    INNER JOIN studied ON student.regno = studied.regno
                    INNER JOIN course ON studied.cid = course.cid
                    WHERE studied.yearofstudy = %s order by student.regno
                    """,
                    [year_name]
                )
                student_data = cursor.fetchall()  
                cursor.execute("""SELECT count(distinct(student.regno)) as register_number from student inner join studied on student.regno=studied.regno 
                    where studied.yearofstudy = %s """ 
                    ,[year_name]
                ) 
                nstudents=cursor.fetchone()
                
        else:
            student_data = None 
            nstudents=0

        return render(request, 'tot_stu_in_a_year.html', {'student_data': student_data ,'nstudents':nstudents,'show_message': request.method == 'POST' and not student_data})
    return render(request, 'tot_stu_in_a_year.html') 


def topper_list(request):

    if request.method == 'GET':
        subject_name = request.GET.get('subject_name', '') 
        num=request.GET.get('num', '')  
        if num=='':
            num=3 
        if subject_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT student.regno as register_number,student.sname AS student_name,studied.ssn_marks,studied.yearofstudy as year
                    FROM student
                    INNER JOIN studied ON student.regno = studied.regno
                    INNER JOIN course ON studied.cid = course.cid
                    WHERE course.title = %s order by studied.ssn_marks  desc
                    
                    """,[subject_name]
                )
                student_data = cursor.fetchall() 
                nstudents=len(student_data) 
                student_data=student_data[0:int(num)]
                
                
        else:
            student_data = None 
            nstudents=0

        return render(request, 'topper.html', {'student_data': student_data ,'nstudents':nstudents,'show_message': request.method == 'POST' and not student_data})
    return render(request, 'topper.html') 


# from django.shortcuts import render
# from django.db import connection

# def fetch_student_data(request):
#     if request.method == 'GET':
#         student_name = request.GET.get('student_name', '')

#         if student_name:
#             with connection.cursor() as cursor:
#                 cursor.execute(
#                     """
#                     SELECT students.name AS student_name, course.name AS course_name, studied.grade 
#                     FROM students
#                     INNER JOIN studied ON students.id = studied.student_id
#                     INNER JOIN course ON studied.course_id = course.id
#                     WHERE students.name = %s
#                     """,
#                     [student_name]
#                 )
#                 student_data = cursor.fetchall()
#         else:
#             student_data = None

#         return render(request, 'student_data.html', {'student_data': student_data ,'show_message': request.method == 'POST' and not student_data})
#     return render(request, 'student_data.html')








