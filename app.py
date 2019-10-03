from flask import Flask, request, json
from pyqrcode import QRCode
import pymysql.cursors
import datetime
import random

app = Flask(__name__)

try:
    connection = pymysql.connect(host='127.0.0.1',
                                 user='root',
                                 password='root',
                                 db='thesis',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    print('all fine')

except Exception as e:
    print('connection failed')
    print(e)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/api/student/signup', methods=['POST'])
def signup():
    name = request.get_json()['name']
    student_num = request.get_json()['studentNum']
    password = request.get_json()['password']
    status = 1000
    message = "failure"
    user_id = 0
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from users where studentNum = " + student_num
            cursor.execute(check)
            result = cursor.fetchall()
            if result.__len__() is 0:
                sql = "INSERT INTO users (name, studentNum, password, created_at) VALUES (%s, %s, %s, %s)"
                now = datetime.datetime.now()
                time_format = now.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(sql, (name, student_num, password, time_format))
                user_id = cursor.lastrowid
                connection.commit()
                status = 0
                message = "success"
            else:
                status = 100
                message = "duplicate"
    except Exception as exception:
        message = exception
        status = 200
    finally:
        return json.dumps({"statusCode": status, "code": message, "userId": user_id}), 200


@app.route('/api/student/login', methods=['POST'])
def login():
    student_num = request.get_json()['studentNum']
    password = request.get_json()['password']
    status = 1000
    message = "failure"
    user_id = 0
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from users where studentNum = " + student_num
            cursor.execute(check)
            result = cursor.fetchall()
            if result.__len__() is not 0:
                inserted_password = result[0]['password']
                if inserted_password == password:
                    user_id = result[0]['id']
                    status = 0
                    message = "success"
                else:
                    status = 100
                    message = "wrongPassword"
            else:
                status = 200
                message = "notRegistered"
    except Exception as exception:
        message = exception
        status = 300
    finally:
        return json.dumps({"statusCode": status, "code": message, "userId": user_id}), 200


@app.route('/api/prof/class/create', methods=['GET'])
def new_class():
    name = request.args.get('name')
    days_begin = request.args.get('daysBegin')
    times_begin = request.args.get('timesBegin')
    place = request.args.get('place')
    password = request.args.get('password')
    status = 1000
    message = "failure"
    class_id = 0
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO class (name, days_begin, times_begin, place, password, created_at) " \
                  "VALUES (%s, %s, %s, %s, %s, %s)"
            now = datetime.datetime.now()
            time_format = now.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (name, days_begin, times_begin, place, password, time_format))
            class_id = cursor.lastrowid
            connection.commit()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 200
    finally:
        return json.dumps({"statusCode": status, "code": message, "class_id": class_id}), 200


@app.route('/api/prof/session/start', methods=['GET'])
def start():
    name = request.args.get('name')
    class_id = request.args.get('classId')
    session_id = 0
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO session (name, class_id, created_at) VALUES (%s, %s, %s)"
            now = datetime.datetime.now()
            time_format = now.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (name, class_id, time_format))
            session_id = cursor.lastrowid
            connection.commit()
            message = "success"
            status = 0
    except Exception as exception:
        message = exception
        status = 200
    finally:
        return json.dumps({"statusCode": status, "code": message, "session_id": session_id}), 200


@app.route('/api/prof/qr/next', methods=['GET'])
def next_qr():
    session_id = request.args.get('sessionId')
    try:
        with connection.cursor() as cursor:
            random_num = random.randint(10000, 99999)
            qr_string = "_{}_{}".format(session_id, random_num)
            qr_code = QRCode(qr_string)
            qr_code.svg('C:\Apache24\htdocs\qr.svg', scale=5)
            sql = "update session set qr = %s, updated_at = %s where id = %s"
            now = datetime.datetime.now()
            time_format = now.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(sql, (qr_string, time_format, session_id))
            connection.commit()
    except Exception as exception:
        return exception
    finally:
        return "http://localhost/qr.svg"


@app.route('/api/student/sub/class', methods=['POST'])
def subscribe():
    user_id = request.get_json()['userId']
    class_id = request.get_json()['classId']
    input_password = request.get_json()['password']
    status = 1000
    message = "failure"
    subscription_id = 0
    try:
        with connection.cursor() as cursor:
            check = "SELECT password from class where id = %s"
            cursor.execute(check, class_id)
            result = cursor.fetchall()
            if result.__len__() is not 0:
                password = result[0]['password']
                if password == input_password:
                    sql = "INSERT INTO subscription (class_id, user_id, created_at) VALUES (%s, %s, %s)"
                    now = datetime.datetime.now()
                    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(sql, (class_id, user_id, time_format))
                    connection.commit()
                    subscription_id = cursor.lastrowid
                    status = 0
                    message = "success"
                else:
                    status = 100
                    message = "wrongPassword"
            else:
                status = 200
                message = "wrongClassId"
    except Exception as exception:
        message = exception
        status = 300
    finally:
        return json.dumps({"statusCode": status, "code": message, "subscriptionId": subscription_id}), 200


@app.route('/api/student/qr/validate', methods=['POST'])
def validate():
    user_id = request.get_json()['userId']
    input_qr = request.get_json()['qr']
    class_id = request.get_json()['classId']
    status = 1000
    message = "failure"
    presence_id = 0
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from class where id = %s"
            cursor.execute(check, class_id)
            result = cursor.fetchall()
            if result.__len__() is not 0:
                query = "SELECT * from subscription where class_id = %s and user_id = %s"
                cursor.execute(query, (class_id, user_id))
                res = cursor.fetchall()
                if res.__len__() is not 0:
                    session_id = input_qr.split('_')[1]
                    q = "SELECT qr from session where id = %s"
                    cursor.execute(q, session_id)
                    ans = cursor.fetchall()
                    if ans.__len__() is not 0:
                        qr = ans[0]['qr']
                        if qr == input_qr:
                            sql = "INSERT INTO presence (class_id, user_id, session_id, created_at) VALUES (%s, %s, %s, %s)"
                            now = datetime.datetime.now()
                            time_format = now.strftime("%Y-%m-%d %H:%M:%S")
                            cursor.execute(sql, (class_id, user_id, session_id, time_format))
                            connection.commit()
                            presence_id = cursor.lastrowid
                            status = 0
                            message = "success"
                        else:
                            status = 100
                            message = "wrongQrCode"
                    else:
                        status = 200
                        message = "wrongSessionId"
                else:
                    status = 300
                    message = "notSubscribed"
            else:
                status = 400
                message = "wrongClassId"
    except Exception as exception:
        status = 500
        message = exception
    finally:
        return json.dumps({"statusCode": status, "code": message, "presenceId": presence_id}), 200


@app.route('/api/prof/student/add', methods=['GET'])
def add_student_presence():
    user_id = request.args.get('userId')
    session_id = request.args.get('sessionId')
    class_id = request.args.get('classId')
    status = 1000
    message = "failure"
    presence_id = 0
    try:
        with connection.cursor() as cursor:
            check = "SELECT user_id from presence where session_id = %s and user_id = %s"
            cursor.execute(check, (session_id, user_id))
            result = cursor.fetchall()
            if result.__len__() is 0 :
                sql = "SELECT user_id from subscription where user_id = %s and class_id = %s "
                cursor.execute(sql, (user_id, class_id))
                res = cursor.fetchall()
                if res.__len__() is not 0:
                    query = "INSERT INTO presence (class_id, user_id, session_id, created_at) VALUES (%s, %s, %s, %s)"
                    now = datetime.datetime.now()
                    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute(query, (class_id, user_id, session_id, time_format))
                    connection.commit()
                    presence_id = cursor.lastrowid
                    status = 0
                    message = "success"
                else:
                    status = 100
                    message = "notSubscribed"
            else:
                status = 200
                message = "userExists"
    except Exception as exception:
        message = exception
        status = 300
    finally:
        return json.dumps({"statusCode": status, "code": message, "presenceId": presence_id}), 200


@app.route('/api/prof/student/delete', methods=['GET'])
def remove_student_presence():
    presence_id = request.args.get('presenceId')
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            check = "DELETE from presence where id = %s"
            cursor.execute(check, presence_id)
            connection.commit()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 200
    finally:
        return json.dumps({"statusCode": status, "code": message}), 200


@app.route('/api/both/class/list', methods=['GET'])
def get_class_list():
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            check = "SELECT id, name from class"
            cursor.execute(check)
            result = cursor.fetchall()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 100
    finally:
        return json.dumps({"statusCode": status, "code": message, "data": result}), 200


@app.route('/api/student/class/<class_id>/<user_id>', methods=['GET'])
def get_class_student(class_id, user_id):
    status = 1000
    message = "failure"
    subscribed = False
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from subscription where class_id = %s and user_id = %s"
            cursor.execute(check, (class_id, user_id))
            res = cursor.fetchall()
            if res.__len__() is not 0:
                subscribed = True
            sql = "SELECT * from class where id = %s"
            cursor.execute(sql, class_id)
            result = cursor.fetchall()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 100
    finally:
        return json.dumps({"statusCode": status, "code": message, "data": result, "subscribed": subscribed}), 200


@app.route('/api/prof/class/<class_id>', methods=['GET'])
def get_class_prof(class_id):
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from class where id = %s"
            cursor.execute(check, class_id)
            result = cursor.fetchall()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 100
    finally:
        return json.dumps({"statusCode": status, "code": message, "data": result}), 200


@app.route('/api/student/class/presence/list/<class_id>/<user_id>', methods=['GET'])
def get_presence_class_student(class_id, user_id):
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from subscription where class_id = %s and user_id = %s"
            cursor.execute(check, (class_id, user_id))
            result = cursor.fetchall()
            if result.__len__() is not 0:
                sql = "select * from session where class_id in " \
                      "(select class_id from subscription where user_id = %s) " \
                      "and id not in (SELECT session_id from presence where user_id = %s and class_id = %s)"
                cursor.execute(sql, (user_id, user_id, class_id))
                result = cursor.fetchall()
                status = 0
                message = "success"
            else:
                status = 100
                message = "notSubscribed"
    except Exception as exception:
        message = exception
        status = 200
    finally:
        return json.dumps({"statusCode": status, "code": message, "data": result}), 200


@app.route('/api/prof/class/delete/<class_id>', methods=['GET'])
def remove_class(class_id):
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            check = "DELETE from presence where class_id = %s"
            cursor.execute(check, class_id)
            connection.commit()
            sql = "DELETE from session where class_id = %s"
            cursor.execute(sql, class_id)
            connection.commit()
            q = "DELETE from subscription where class_id = %s"
            cursor.execute(q, class_id)
            connection.commit()
            query = "DELETE from class where id = %s"
            cursor.execute(query, class_id)
            connection.commit()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 100
    finally:
        return json.dumps({"statusCode": status, "code": message}), 200


@app.route('/api/student/profile/<user_id>', methods=['GET'])
def student_profile(user_id):
    status = 1000
    message = "failure"
    try:
        with connection.cursor() as cursor:
            check = "SELECT * from users where id = %s"
            cursor.execute(check, user_id)
            result = cursor.fetchall()
            status = 0
            message = "success"
    except Exception as exception:
        message = exception
        status = 100
    finally:
        return json.dumps({"statusCode": status, "code": message, "data": result}), 200


if __name__ == '__main__':
    app.run()
