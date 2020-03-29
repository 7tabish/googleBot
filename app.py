from flask import Flask,jsonify,make_response,render_template,redirect,request,session
import requests
import csv
from datetime import datetime
import json
import time,re

app = Flask(__name__)
app.secret_key = "super secret key"




@app.route('/datePicker',methods=['GET'])
def datePicker():
    return render_template('datePicker.html')


@app.route('/',methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/authenticate',methods=['POST'])
def authenticate():
    client_id=request.form['id']
    client_secret=request.form['secret']
    session['client_id']=client_id
    session['client_session']=client_secret
    url='''https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/gmail.readonly&access_type=offline&include_granted_scopes=true&response_type=code&redirect_uri=http://127.0.0.1:5000/generateToken&client_id={}'''.format(client_id)
    return redirect(url)

@app.route('/wait',methods=['GET'])
def wait():
    return render_template('wait.html')

@app.route('/generateToken',methods=['GET'])
def generateToken():
    code=request.args.get('code')
    client_id=session['client_id']
    client_secret=session['client_session']
    url=f'''
    https://oauth2.googleapis.com/token?client_id={client_id}&grant_type=authorization_code&code={code}&redirect_uri=http://127.0.0.1:5000/generateToken&client_secret={client_secret}'''

    response=requests.post(url=url)
    response_data=json.loads(response.text)
    print(response_data)
    session['accessToken']=response_data['access_token']

    return render_template('datePicker.html')





@app.route('/getMessage',methods=['GET'])
def getMessage():
    dateFrom=request.args.get('dateFrom')
    dateTo=request.args.get('dateTo')
    dateFrom= datetime.strptime(str(dateFrom), '%Y-%m-%d')
    dateTo = datetime.strptime(str(dateTo), '%Y-%m-%d')

    print('in message')
    accessToken=session['accessToken']
    accessToken="Bearer "+accessToken
    url = 'https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=50'
    response = requests.get(url=url, headers={
        "Authorization": accessToken})
    messaages = json.loads(response.text)
    messages_id = []
    csv = 'Id,ThreadId,Date,From,Subject,Message\n'
    for message in messaages['messages']:
        messages_id.append(message['id'])
    for each_message in messages_id:
        get_msg_url=' https://www.googleapis.com/gmail/v1/users/me/messages/'+each_message
        response1=requests.get(url=get_msg_url,headers={"Authorization":accessToken})

        message_data=json.loads(response1.text)
        id=message_data['id']
        threadId=message_data['threadId']
        snippet=message_data['snippet']
        message_payload=message_data['payload']
        msg_date=None
        msg_from=None
        msg_subject=None
        for header in message_payload['headers']:
            if header['name']=='Date':
                msg_date=header['value']
                msg_date=re.sub(r" ?\([^)]+\)", "", msg_date)
                dateObj=time.strptime(msg_date, "%a, %d %b %Y %H:%M:%S %z")

                day = dateObj.tm_mday
                month = dateObj.tm_mon
                year = dateObj.tm_year

                #save msg_date in csv
                msg_date = str(year) + '-' + str(month) + '-' + str(day)
                mailDateObj = datetime.strptime(msg_date, '%Y-%m-%d')
            if header['name']=='From':
                msg_from=header['value']
            if header['name']=='Subject':
                 msg_subject=header['value']
        if mailDateObj >= dateFrom and mailDateObj <= dateTo:
            csv=csv+id+","+threadId+","+msg_date+","+msg_from+","+msg_subject+","+snippet+"\n"

    response = make_response(csv)
    cd = 'attachment; filename=mycsv.csv'
    response.headers['Content-Disposition'] = cd
    response.mimetype = 'text/csv'

    return response
    # return jsonify(
    #     id=id,
    #     message=snippet,
    #     msg_date=msg_date,
    #     msg_from=msg_from,
    #     msg_subject=msg_subject,
    #     msg_ids=messages_id
    # )

@app.route('/csv/')
def download_csv():
    csv = 'id,subject,from,message,date\n'
    csv=csv+'id1,subject1,from1,message1,date1'
    response = make_response(csv)
    cd = 'attachment; filename=mycsv.csv'
    response.headers['Content-Disposition'] = cd
    response.mimetype='text/csv'

    return response

if __name__ == '__main__':
    app.run()
