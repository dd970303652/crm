from django.shortcuts import render, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from .models import User
from django.http import JsonResponse
from email.header import Header  # 如果包含中文，需要通过Header对象进行编码
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib  # 负责发送邮件
import uuid
from datetime import datetime, timedelta
from hashlib import md5

# Create your views here.
#跳转登录和注册页面
def login_register(request):
    return render(request,'login_register.html')


#验证用户名是否唯一
@require_POST
def unique_username(request):
    try:
        #获取页面信息
        username=request.POST.get('username')
        #查询用户是否存在
        User.objects.get(username=username)
        #如果存在用户则返回页面json
        return JsonResponse({'code':400,'msg':'用户名已存在'})
    except User.DoesNotExist as e:
        return JsonResponse({'code':200,'msg':'注册成功!'})

#验证邮箱是否唯一
def unique_email(request):
    try:
        #获取页面信息
        email=request.POST.get('email')
        #查询用户是否存在
        User.objects.get(email=email)
        #如果存在用户则返回页面json
        return JsonResponse({'code': 400, 'msg': '邮箱已存在'})
    except User.DoesNotExist as e:
        return JsonResponse({'code': 200, 'msg': '注册成功!'})


def format_mail(addr):
    name,email_addr=parseaddr(addr)
    #可能存在中文则需要进行编码
    return formataddr((Header(name,'utf-8').encode('utf-8'),email_addr))



@require_POST
def email_send(request):
    try:
        # -----------------准备数据开始----------------------
        # 发件人邮箱
        send_email = '15773001124@163.com'
        # 授权码
        password = 'sxt0523'
        # 邮件发送的服务地址
        email_server = 'smtp.163.com'
        # 收件人邮箱
        recv_email = request.POST.get('email')

        #获取用户名
        username=request.POST.get('username')
        #获取密码
        u_pwd=request.POST.get('password')
        #使用md5加密
        u_pwd=md5(u_pwd.encode(encoding='utf-8')).hexdigest()
        #激活码处理
        code=''.join(str(uuid.uuid4())).split('-')
        #10分钟后的时间戳
        td=timedelta(minutes=10)
        ts=datetime.now()+td
        #取时间戳小数点前的部分
        ts=str(ts.timestamp()).split('.')[0]

        # ---------------插入数据库数据-------------------
        user=User(username=username,password=u_pwd,email=recv_email,code=code,timestamp=ts)
        user.save()
                # ------------------------构建邮件对象开始---------------
        '''
            构建邮件内容对象
                第一个参数是邮件内容
                第二个参数是MIME,必须是plain也就是text/plain否则中文不显示
                第三个参数是编码          
        '''
        html = '''
            <html>
                <body>
                   <div>
                        Email 地址验证<br>
                        这封信是由 上海尚学堂 发送的。<br>
                        您收到这封邮件，是由于在 上海尚学堂CRM系统 进行了新用户注册，或用户修改 Email 使用了这个邮箱地址。<br>
                        如果您并没有访问过 上海尚学堂CRM，或没有进行上述操作，请忽略这封邮件。您不需要退订或进行其他进一步的操作。<br>
                        ----------------------------------------------------------------------<br>
                         帐号激活说明<br>
                        ----------------------------------------------------------------------<br>
                        如果您是 上海尚学堂CRM 的新用户，或在修改您的注册 Email 时使用了本地址，我们需要对您的地址有效性进行验证以避免垃圾邮件或地址被滥用。<br>
                        您只需点击下面的链接激活帐号即可：<br>
                        <a href="http://www.crm.com/active_accounts/?username={}&code={}&timestamp={}">http://www.crm.com/active_accounts/?username={}&amp;code={}&amp;timestamp={}</a><br/>
                        感谢您的访问，祝您生活愉快！<br>
                        此致<br>
                         上海尚学堂 管理团队.
                        </div>
                </body>
            </html>
        '''.format(username,code,ts,username,code,ts)
        msg = MIMEText(html, 'html', 'utf-8')

        # 标准邮件需要三个头部信息: From  To  和subject
        # 设置发件人和收件人的信息
        # 比如:尚学堂<java_mail01@163.com>
        # 发件人
        msg['From'] = format_mail('士官长<%s>' % send_email)
        # 收件人
        msg['TO'] = format_mail(recv_email)
        # 主题
        msg['Subject'] = str(Header('晚上搞起啊!', 'utf-8'))
        # -------------------构建邮件对象结束------------------

        # ----------------------发送邮件开始-------------------
        # 创建发送邮件服务器的对象
        server = smtplib.SMTP(email_server, 25)
        # 设置debug级别0就不打印发送日志,1打印
        server.set_debuglevel(1)
        # 登录发件邮箱
        server.login(send_email, password)
        # 调用发送方法  第一个参数是发送者邮箱,第二个是接收邮箱,第三个是发送内容
        server.sendmail(send_email, [recv_email], msg.as_string())
        # 关闭发送
        server.quit()
        # ---------邮件发送结束-------------

        #返回页面提示信息
        return JsonResponse({'code':200,'msg':'注册成功!'})
    except smtplib.SMTPException as e:
        #返回页面提示信息
        return JsonResponse({'code':400,'msg':'注册失败!'})


#激活账号
@require_GET
def action_accounts(request):
    try:
        #获取用户名
        username=request.GET.get('username')
        #获取激活码
        code=request.GET.get('code')
        #获取过期时间
        ts=request.GET.get('timestamp')
        #根据用户名和激活码查询是否账号是否存在
        user=User.objects.get(username=username,code=code,timestamp=ts)
        #根据过期时间判断账号是否有效
        now_ts=int(str(datetime.now().timestamp()).split('.')[0])
        if now_ts>int(ts):
            #链接失效,返回提示信息并删除数据库信息
            user.delete()
            return HttpResponse('<h1>此链接已失效,请重新注册&nbsp;&nbsp;<a href="http://www.crm.com/login_register/">上海尚学堂CRM系统</a></h1>')
        #清除激活码
        user.code=''
        #设置账号有效
        user.status=1
        #保存到数据库
        user.save()

        #返回提示信息
        return HttpResponse( '<h1>帐号激活成功，请前往系统登录&nbsp;&nbsp;<a href="http://www.crm.com/login_register/">上海尚学堂CRM系统</a></h1>')
    except Exception as e:
        #判断是否是链接过期导致的错误
        if isinstance(e,User.DoesNotExist):
            return HttpResponse('<h1>该链接已失效，请重新注册&nbsp;&nbsp;<a href="http://www.crm.com/login_register/">上海尚学堂CRM系统</a></h1>')
        return HttpResponse('<h1>不好意思，网络出现了波动，激活失败，请重新尝试</h1>')


