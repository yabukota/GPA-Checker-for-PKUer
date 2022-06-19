import re
import requests
import time
import smtplib
import json
from getpass import getpass
from email.mime.text import MIMEText
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import datetime


class portal:
    oauthLogin = 'https://iaaa.pku.edu.cn/iaaa/oauthlogin.do'
    ssoLogin = 'http://portal.pku.edu.cn/portal2017/ssoLogin.do'
    retrScores = 'https://portal.pku.edu.cn/portal2017/bizcenter/score/retrScores.do'
    userName = ''
    password = ''
    getGPAbyXh = 'https://portal.pku.edu.cn/portal2017/bizcenter/score/getGPAbyXh.do'
    xnd = '21-22' # TODO：学年度
    xq = '2' # TODO：学期
    send_mail_addr = ''
    send_mail_password = ''
    send_mail_server = ''
    receive_mail_addr = ''
    sleep_time=30
    def __init__(self,send_addr=None, send_pass=None, send_server=None, receive_addr=None, sleep_time=30):
        self.send_mail_addr = send_addr
        self.send_mail_password = send_pass
        self.send_mail_server = send_server
        self.receive_mail_addr = receive_addr
        self.sleep_time = sleep_time
        self.sess = requests.Session()
        self.sess.headers.update({'User-Agent': 'Chrome'})
        self.sess.keep_alive = False
        requests.adapters.DEFAULT_RETRIES = 5
    def getNext(self, url, params=[], referer='', verify=False):
        if referer != '':
            self.sess.headers.update({'Referer': referer})
        while True:
            try:
                r = self.sess.get(url, params=params,
                                  timeout=10, verify=verify)
                break
            except:
                print("Get process error")
                time.sleep(10)
        return r.text

    def postNext(self, url, data=[], referer='', verify=False):
        if referer != '':
            self.sess.headers.update({'Referer': referer})
        r = self.sess.post(url, data, timeout=10, verify=verify)
        while True:
            try:
                r = self.sess.post(url, data, timeout=10, verify=verify)
                break
            except:
                print("Post process error")
                time.sleep(10)
        return r.text


    def login(self):
        if self.userName == '':
            self.userName = input("Please input your student ID:")
        if self.password == '':
            self.password = getpass("Please input your password:")
        self.data = {'userName': '%s' % self.userName, 'password': '%s' % self.password,
        'appid':'portal2017','redirUrl': 'https://portal.pku.edu.cn/portal2017/ssoLogin.do',
        'randCode':'','smsCode':'','otpCode':''}
        tot = 0       
        while True:
            cont = self.postNext(self.oauthLogin, self.data)
            if cont.find('token') != -1:
                break
            tot += 1
            time.sleep(1)
            if tot > 10:
                print('登陆错误超过10次，请检查输入密码是否正确，请尝试重新登陆!如密码正确，请检查网络。\n')
                self.userName = input("Please input your student ID:")
                self.password = getpass("Please input your password:")
                self.data = {'userName': '%s' % self.userName, 'password': '%s' % self.password,
        'appid':'portal2017','redirUrl': 'https://portal.pku.edu.cn/portal2017/ssoLogin.do',
        'randCode':'','smsCode':'','otpCode':''}
        print(cont)
        p = {}
        p['token'] = re.search(r'n":"(.*?)"', cont).group(1)
        p['_rand'] = 0.7555405047770082
        cont = self.getNext(self.ssoLogin, p)
    def getOutput(self):
        cont = self.postNext(self.retrScores)
        if cont.find('cjxx') == -1:
            return 'There is some mistake with your account'
        s = json.loads(cont)['cjxx']
        output = set()
        for semester in range(len(s)):
            if s[semester]['xnd'] == self.xnd and s[semester]['xq'] == self.xq: 
                # 只查本学年本学期的成绩
                classList = s[semester]['list']
                for classItem in classList:
                    output.add(classItem['kcmc'] + '   Grade:' +                         classItem['xqcj'] + '   GPA:' + classItem['jd'] + '\n')
        return output
    def autoCheck(self):
        self.output = set()
        while True:
            output = self.getOutput()
            check_message = '无新增成绩'
            if output != self.output:
                new_course = output - self.output
                self.sendMailto(new_course, output)
                check_message = '有新增成绩, 已发送邮箱'
            self.output = output
            print(f'最后查询时间: {datetime.datetime.now()}, {check_message}')
            time.sleep(sleep_time)

    def sendMailto(self, new_course, all_course):
        mailserver = smtplib.SMTP(self.send_mail_server, 25)
        mailserver.login(self.send_mail_addr, self.send_mail_password)
        
        message = '新增成绩:\n' + ''.join(new_course) + '\n'
        message += '本学期全部成绩:\n' + ''.join(all_course)
        msg = MIMEText(message, 'plain', 'utf-8')
        
        new_course_name = []
        for course in new_course:
            new_course_name.append(course.split()[0])
        msg['Subject'] = f"新增成绩：{','.join(new_course_name)}"
        msg['from'] = self.send_mail_addr
        msg['to'] = self.receive_mail_addr
        mailserver.sendmail(self.send_mail_addr, [
                            self.receive_mail_addr], msg.as_string())
        mailserver.quit()


if __name__ == '__main__':
    
    send_mail_addr = 'xxxxxxxx@qq.com' # TODO：发送邮箱地址
    send_mail_password = 'xxxxxxxx' # TODO：发送邮箱的授权码
                                          # 注意不是密码
                                          # 请参考https://blog.csdn.net/qq_45328505/article/details/122115459
    send_mail_server = 'smtp.xxxx.xxxx' # TODO：发件服务器地址
                                   # 163邮箱为smtp.163.com
                                   # qq邮箱为smtp.qq.com
                                   # 北大邮箱：smtp.pku.edu.cn
    receive_mail_addr = 'xxxxxxxxx@pku.edu.cn' # TODO：接收邮箱地址
    sleep_time = 30 # TODO：设置多少秒查询一次成绩,默认为30s
    
    #第一次会主动给你所在的邮箱发一封邮件，如果能收到邮件，表示程序成功。
    
    portal = portal(send_mail_addr, send_mail_password, send_mail_server, receive_mail_addr, sleep_time)
    portal.login()
    portal.autoCheck()
