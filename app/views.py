from django.shortcuts import render, redirect, HttpResponse
from app import models
import uuid
from utils.pay import AliPay


# Create your views here.
def goods(request):
    goods_list = models.Goods.objects.all()
    # print(goods_list)
    # <QuerySet [<Goods: Goods object (1)>, <Goods: Goods object (2)>, <Goods: Goods object (3)>, <Goods: Goods object (4)>]>
    return render(request, 'goods.html', {'goods_list': goods_list})


def purchase(request, goods_id):
    # 通过goods对象获取需要的商品价格和商品名称
    goods_obj = models.Goods.objects.get(id=goods_id)  # 用pk=goods_id也是可以的
    # print(goods_obj.goods_name,goods_obj.goods_price)
    '''
    生成订单
    '''
    # 产生一个uuid，作为订单号
    order_number = str(uuid.uuid4())
    models.Order.objects.create(
        order_number=order_number,
        goods=goods_obj  # goods_id=goods_obj.id,
    )
    '''
    跳转到支付宝支付页面
    '''
    # 实例化AliPay
    alipay = AliPay(
        appid="2016101200668044",  # APPID
        app_notify_url='http://106.12.115.136:8000/check_order/',  # 支付宝会向这个地址发送post请求
        return_url='http://127.0.0.1:8000/show_msg/',  # 支付宝会向这个地址发送get请求
        app_private_key_path='keys/app_private_2048.txt',  # 应用私钥
        alipay_public_key_path='keys/alipay_public_2048.txt',  # 支付宝公钥
        debug=True,  # 默认是False
    )
    # 定义请求地址传入的参数
    query_params = alipay.direct_pay(
        subject=goods_obj.goods_name,  # 商品描述
        out_trade_no=order_number,  # 订单号
        total_amount=goods_obj.goods_price,  # 交易金额(单位是元，保留两位小数)
    )
    # 需要跳转到支付宝的支付页面，所以需要生成跳转的url
    pay_url = 'https://openapi.alipaydev.com/gateway.do?{0}'.format(query_params)
    return redirect(pay_url)


def show_msg(request):
    if request.method == 'GET':
        alipay = AliPay(
            appid="2016101200668044",  # APPID
            app_notify_url='http://106.12.115.136:8000/check_order/',
            return_url='http://127.0.0.1:8000/show_msg/',
            app_private_key_path='keys/app_private_2048.txt',  # 应用私钥
            alipay_public_key_path='keys/alipay_public_2048.txt',  # 支付宝公钥
            debug=True,  # 默认是False
        )
        params = request.GET.dict()  # 获取请求携带的参数并转换成字典类型
        print(
            request.GET)  # <QueryDict: {'charset': ['utf-8'], 'out_trade_no': ['04f09b6f-e792-4a1d-8dbc-c68f1d046622'], ……}
        print(params)  # {'charset': 'utf-8', 'out_trade_no': '04f09b6f-e792-4a1d-8dbc-c68f1d046622',……}
        sign = params.pop('sign', None)  # 获取sign的值
        # 对sign参数进行验证
        status = alipay.verify(params, sign)
        if status:
            return render(request, 'show_msg.html', {'msg': '支付成功'})
        else:
            return render(request, 'show_msg.html', {'msg': '支付失败'})
    else:
        return render(request, 'show_msg.html', {'msg': '只支持GET请求，不支持其它请求'})


def check_order(request):
    '''
    支付宝通知支付的结果信息，如果支付成功可以用来修改订单的状态
    :param request:
    :return:
    '''

    if request.method == 'POST':
        alipay = AliPay(
            appid="2016101200668044",  # APPID
            app_notify_url='http://106.12.115.136:8000/check_order/',  # 支付宝会向这个地址发送post请求
            return_url='http://127.0.0.1:8000/show_msg/',  # 支付宝会向这个地址发送get请求
            app_private_key_path='keys/app_private_2048.txt',  # 应用私钥
            alipay_public_key_path='keys/alipay_public_2048.txt',  # 支付宝公钥
            debug=True,
        )
        # print('request.body：', request.body)  # 是字节类型,b'gmt_create=2019-09-21+17%3A00%3A15&charset=utf-8&……
        body_str = request.body.decode('utf-8')  # 转成字符串
        # print('body_str：', body_str)
        from urllib.parse import parse_qs
        post_data = parse_qs(body_str)  # 根据&符号分割
        # print(post_data)  # post_data是一个字符串
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]
        sign = post_dict.pop('sign', None)
        status = alipay.verify(post_dict, sign)
        print(status)
        if status:  # 支付成功
            out_trade_no = post_dict['out_trade_no']
            return_value = models.Order.objects.filter(order_number=out_trade_no).update(order_status=1)
            print('return_value', return_value)
            return HttpResponse('success')  # 向支付宝返回success,表示接收到请求
        else:
            return HttpResponse('支付失败')
    else:
        return HttpResponse('只支持POST请求')


def order_list(request):
    order_obj = models.Order.objects.all()
    return render(request, 'order_list.html', {'order_obj': order_obj})
