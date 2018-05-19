# -*- coding: utf-8 -*-
from copy import deepcopy
import logging

from datetime import datetime
from sqlalchemy import func, desc

from configs.config import db, ERR_WRONG_ITEM, SUCCESS, ERR_WRONG_USER_ITEM, CONSUMPTION_TASK_TYPE
from core.consumption_core import add_task_to_consumption_task
from core.material_library_core import generate_material_into_frontend_by_material_id, \
    analysis_frontend_material_and_put_into_mysql
from core.qun_manage_core import get_a_chatroom_dict_by_uqun_id
from models.android_db_models import AContact
from models.batch_sending_models import BatchSendingTaskInfo, BatchSendingTaskTargetRelate, \
    BatchSendingTaskMaterialRelate
from models.material_library_models import MaterialLibraryUser
from models.production_consumption_models import ConsumptionTaskStream, ConsumptionTask
from models.qun_friend_models import UserQunRelateInfo, UserQunBotRelateInfo
from models.user_bot_models import UserBotRelateInfo, BotInfo
from utils.u_time import datetime_to_timestamp_utc_8

logger = logging.getLogger('main')


def get_batch_sending_task(user_info, task_per_page, page_number):
    """
    根据一个人，把所有的这个人可见的群发任务都出来
    :param user_info:
    :return:
    """
    bs_task_info_list = db.session.query(BatchSendingTaskInfo).filter(
        BatchSendingTaskInfo.user_id == user_info.user_id,
        BatchSendingTaskInfo.is_deleted == 0).order_by(
        desc(BatchSendingTaskInfo.task_create_time)).limit(task_per_page).offset(task_per_page * page_number).all()
    result = []
    for bs_task_info in bs_task_info_list:
        status, task_detail_res = get_task_detail(bs_task_info=bs_task_info)
        if status == SUCCESS:
            result.append(deepcopy(task_detail_res))
        else:
            logger.error(u"部分任务无法读取. sending_task_id: %s." % bs_task_info.sending_task_id)

    return SUCCESS, result


def get_task_detail(sending_task_id=None, bs_task_info=None):
    """
    读取一个任务的所有信息
    """
    if not sending_task_id and not bs_task_info:
        raise ValueError(u"传入参数有误，不能传入空参数")

    if sending_task_id:
        bs_task_info = db.session.query(BatchSendingTaskInfo).filter(
            BatchSendingTaskInfo.sending_task_id == sending_task_id).first()

    if not bs_task_info:
        return ERR_WRONG_ITEM, None

    res = dict()
    res.setdefault("sending_task_id", sending_task_id)
    res.setdefault("task_covering_chatroom_count", bs_task_info.task_covering_qun_count)
    res.setdefault("task_covering_people_count", bs_task_info.task_covering_people_count)
    res.setdefault("task_create_time", datetime_to_timestamp_utc_8(bs_task_info.task_create_time))

    temp_tsc = db.session.query(func.count(ConsumptionTaskStream.chatroomname)). \
        filter(ConsumptionTaskStream.task_type == 1,
               ConsumptionTaskStream.task_relevant_id == bs_task_info.sending_task_id).all()

    res.setdefault("task_sended_count", temp_tsc[0][0])

    # TODO-zwf 想办法把失败的读出来
    res.setdefault("task_sended_failed_count", 0)

    # 生成群信息
    res.setdefault("chatroom_list", [])
    bs_task_target_list = db.session.query(BatchSendingTaskTargetRelate).filter(
        BatchSendingTaskTargetRelate.sending_task_id == bs_task_info.sending_task_id).all()
    if not bs_task_target_list:
        return ERR_WRONG_ITEM, None
    uqun_id_list = []
    for bs_task_target in bs_task_target_list:
        uqun_id_list.append(bs_task_target.uqun_id)
    for uqun_id in uqun_id_list:
        status, tcd_res = get_a_chatroom_dict_by_uqun_id(uqun_id=uqun_id)
        if status == SUCCESS:
            res['chatroom_list'].append(deepcopy(tcd_res))
        else:
            pass

    # 生成material信息
    res.setdefault("message_list", [])
    bs_task_material_list = db.session.query(BatchSendingTaskMaterialRelate).filter(
        BatchSendingTaskMaterialRelate.sending_task_id == bs_task_info.sending_task_id).order_by(
        BatchSendingTaskMaterialRelate.send_seq).all()
    if not bs_task_material_list:
        return ERR_WRONG_ITEM, None
    material_id_list = []
    for bs_task_material_relate in bs_task_material_list:
        material_id_list.append(bs_task_material_relate.material_id)
    for material_id in material_id_list:
        temp_material_dict = generate_material_into_frontend_by_material_id(material_id)
        res["message_list"].append(deepcopy(temp_material_dict))

    return SUCCESS, res


def get_task_fail_detail(sending_task_id):
    """
    读取一个任务的任务情况，成功或者失败
    :param sending_task_id:
    :return:
    """


def create_a_sending_task(user_info, chatroom_list, message_list):
    """
    将前端发送过来的任务放入task表，并将任务放入consumption_task
    :return:
    """
    # 先验证各个群情况
    now_time = datetime.now()
    bs_task_info = BatchSendingTaskInfo()
    bs_task_info.user_id = user_info.user_id
    bs_task_info.task_covering_qun_count = 0
    bs_task_info.task_covering_people_count = 0
    bs_task_info.task_status = 1
    bs_task_info.task_status_content = "等待开始"
    bs_task_info.is_deleted = False
    bs_task_info.task_create_time = now_time
    db.session.add(bs_task_info)
    db.session.commit()

    task_covering_qun_count = 0
    task_covering_people_count = 0

    valid_chatroom_list = []
    for uqun_id in chatroom_list:
        uqr_info = db.session.query(UserQunRelateInfo).filter(UserQunRelateInfo.user_id == user_info.user_id,
                                                              UserQunRelateInfo.uqun_id == uqun_id).first()
        if not uqr_info:
            logger.error("没有属于该用户的该群")
            return ERR_WRONG_USER_ITEM

        a_contact = db.session.query(AContact).filter(AContact.username == uqr_info.chatroomname).first()

        if not a_contact:
            logger.error("安卓库中没有该群")
            return ERR_WRONG_USER_ITEM

        task_covering_qun_count += 1
        task_covering_people_count += a_contact.member_count

        bs_task_target = BatchSendingTaskTargetRelate()
        bs_task_target.sending_task_id = bs_task_info.sending_task_id
        bs_task_target.uqun_id = uqun_id
        db.session.add(bs_task_target)
        valid_chatroom_list.append(uqr_info)
    db.session.commit()

    # 处理message，入库material
    valid_material_list = []
    for i, message_info in enumerate(message_list):
        message_return, um_lib = analysis_frontend_material_and_put_into_mysql(user_info.user_id, message_info,
                                                                               now_time, update_material=True)
        if message_return == SUCCESS:
            pass
        elif message_return == ERR_WRONG_ITEM:
            continue

        material_id = um_lib.material_id
        bs_task_material = BatchSendingTaskMaterialRelate()
        bs_task_material.material_id = material_id
        bs_task_material.sending_task_id = bs_task_info.sending_task_id
        bs_task_material.send_seq = i
        db.session.add(bs_task_material)
        valid_material_list.append(um_lib)
    db.session.commit()

    # 更新主库中的数量
    bs_task_info.task_covering_qun_count = task_covering_qun_count
    bs_task_info.task_covering_people_count = task_covering_people_count
    db.session.merge(bs_task_info)
    db.session.commit()

    # 确认任务放入无问题后，将任务发出
    for uqr_info_iter in valid_chatroom_list:
        for um_lib_iter in valid_material_list:
            _add_task_to_consumption_task(uqr_info_iter, um_lib_iter, bs_task_info)
    return SUCCESS


def _add_task_to_consumption_task(uqr_info, um_lib, bs_task_info):
    """
    将任务放入consumption_task
    :return:
    """
    status = add_task_to_consumption_task(uqr_info, um_lib, bs_task_info.user_id,
                                          CONSUMPTION_TASK_TYPE["batch_sending_task"], bs_task_info.sending_task_id)
    return status