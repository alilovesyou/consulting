# utils/states.py
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData

class Registration(StatesGroup):
    fio = State()       
    phone = State()     
    region = State()    
    age = State()     
    confirm = State()

class RegionCB(CallbackData, prefix="reg"):
    name: str

class DistrictCB(CallbackData, prefix="dist"):
    reg_name: str
    name: str

class OrderCourse(StatesGroup):
    payment_method = State() # To'lov usulini kutish
    receipt = State()        # Chek rasmini kutish

class LangCB(CallbackData, prefix="lang"):
    code: str

class PackCB(CallbackData, prefix="pack"):
    lang_code: str
    pack_type: str

class AdminApproveCB(CallbackData, prefix="adm_app"):
    payment_id: int

class AdminRejectCB(CallbackData, prefix="adm_rej"):
    payment_id: int

class AdminGroupCB(CallbackData, prefix="adm_grp"):
    payment_id: int
    group_id: int

class TeacherRegistration(StatesGroup):
    fio = State()
    phone = State()
    region = State()
    age = State()           
    lang = State()
    experience = State() 
    confirm = State()      

class AdminTeacherApproveCB(CallbackData, prefix="adm_t_app"):
    teacher_id: int

class AdminTeacherRejectCB(CallbackData, prefix="adm_t_rej"):
    teacher_id: int

class UploadLesson(StatesGroup):
    title = State()      
    material = State()  

class GroupManageCB(CallbackData, prefix="g_man"):
    group_id: int
    action: str       
class StudentGroupCB(CallbackData, prefix="st_grp"):
    group_id: int

class LessonCB(CallbackData, prefix="st_les"):
    lesson_id: int

class CreateGroup(StatesGroup):
    name = State()
    language = State()
    capacity = State()
    link = State()
    teacher = State()

class AssignTeacherCB(CallbackData, prefix="ass_tch"):
    teacher_id: int
class ResultEntry(StatesGroup):
    title = State()
    score = State()
    comment = State()

class KickRequestState(StatesGroup):
    reason = State()

class TeacherGroupCB(CallbackData, prefix="t_grp"):
    group_id: int
    action: str

class TeacherStudentCB(CallbackData, prefix="t_st"):
    group_id: int
    student_id: int
    action: str

class KickApproveCB(CallbackData, prefix="kick_app"):
    request_id: int

class KickRejectCB(CallbackData, prefix="kick_rej"):
    request_id: int
class AddAdminState(StatesGroup):
    telegram_id = State()
    full_name = State()


class RemoveAdminCB(CallbackData, prefix="rm_admin"):
    telegram_id: int
class LangSelectCB(CallbackData, prefix="ui_lang"):
    lang: str