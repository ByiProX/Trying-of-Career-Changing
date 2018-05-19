# -*- coding: utf-8 -*-

import logging

from core.real_time_quotes_core import switch_func_real_time_quotes, get_rt_quotes_list_and_status, \
    get_rt_quotes_preview
from flask import request

from configs.config import SUCCESS, ERR_PARAM_SET, main_api
from core.user_core import UserLogin
from utils.u_response import make_response

logger = logging.getLogger('main')


@main_api.route('/switch_func_real_time_quotes', methods=['POST'])
def app_switch_func_real_time_quotes():
    status, user_info = UserLogin.verify_token(request.json.get('token'))
    if status != SUCCESS:
        return make_response(status)

    switch = request.json.get('switch')
    if not (switch is True or switch is False):
        return make_response(ERR_PARAM_SET)

    status = switch_func_real_time_quotes(user_info, switch)
    # logger.error("ERR_NOT_IMPLEMENTED 功能未实现，先留出口")

    if status == SUCCESS:
        return make_response(SUCCESS)
    else:
        return make_response(status)


@main_api.route('/get_rt_quotes_list_and_status', methods=['POST'])
def app_get_rt_quotes_list_and_status():
    status, user_info = UserLogin.verify_token(request.json.get('token'))
    if status != SUCCESS:
        return make_response(status)

    task_per_page = request.json.get('page_size')
    page_number = request.json.get('page')
    if not task_per_page:
        logger.warning("没有收到page_size，设置为10")
        task_per_page = 10
    if page_number is None:
        logger.warning("没有收到page_number，设置为0")
        page_number = 0

    # status = SUCCESS
    # logger.error("ERR_NOT_IMPLEMENTED 功能未实现，先留出口")

    # example = [
    #     {
    #         "coin_id": 1,
    #         "coin_name": "比特币",
    #         "logo": "http://"
    #     },
    #     {
    #         "coin_id": 2,
    #         "coin_name": "以太坊",
    #         "logo": "http://"
    #     },
    #     {
    #         "coin_id": 3,
    #         "coin_name": "火币",
    #         "logo": "http://"
    #     },
    # ]
    # example_func = True
    status, res, func_status, count = get_rt_quotes_list_and_status(user_info, task_per_page, page_number)

    if status == SUCCESS:
        return make_response(SUCCESS, coin_list=res, func_real_time_quotes=func_status, count=count)
    else:
        return make_response(status)


@main_api.route('/get_func_real_time_quotes_status', methods=['POST'])
def app_get_func_real_time_quotes_status():
    status, user_info = UserLogin.verify_token(request.json.get('token'))
    if status != SUCCESS:
        return make_response(status)

    return make_response(SUCCESS, func_real_time_quotes=user_info.func_real_time_quotes)


@main_api.route('/get_rt_quotes_preview', methods=['POST'])
def app_get_rt_quotes_preview():
    status, user_info = UserLogin.verify_token(request.json.get('token'))
    if status != SUCCESS:
        return make_response(status)

    coin_id = request.json.get('coin_id')
    if not coin_id:
        return make_response(ERR_PARAM_SET)

    # status = SUCCESS
    # logger.error("ERR_NOT_IMPLEMENTED 功能未实现，先留出口")
    #
    # example = {
    #     "coin_id": coin_id,
    #     "name": 'BTC-比特币',
    #     "logo": './assets/imgs/logo.png',
    #     "keyword_list": ["BTC", "btc", "比特币"],
    #     "price": '64634',
    #     "all_price": '100921亿',
    #     "rank": '第1名',
    #     "coin_num": '3011万',
    #     "add_rate": '+5.73%',
    #     "change_num": '500万'
    # }
    status, res = get_rt_quotes_preview(coin_id)

    if status == SUCCESS:
        return make_response(SUCCESS, coin=res)
    else:
        return make_response(status)