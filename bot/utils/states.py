# utils/states.py
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData


# ==========================================
# USER / STUDENT REGISTRATION
# ==========================================

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


class LangSelectCB(CallbackData, prefix="ui_lang"):
    lang: str


# ==========================================
# COURSE ORDER / PAYMENT
# ==========================================

class OrderCourse(StatesGroup):
    payment_method = State()
    receipt = State()


class LangCB(CallbackData, prefix="lang"):
    code: str


class PackCB(CallbackData, prefix="pack"):
    lang_code: str
    pack_type: str


# Eski payment approve/reject callbacklar.
# Hozircha admin.py va notificationlarda ishlaydi.
class AdminApproveCB(CallbackData, prefix="adm_app"):
    payment_id: int


class AdminRejectCB(CallbackData, prefix="adm_rej"):
    payment_id: int


class AdminGroupCB(CallbackData, prefix="adm_grp"):
    payment_id: int
    group_id: int


# ==========================================
# TEACHER REGISTRATION
# ==========================================

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


# ==========================================
# TEACHER LESSON UPLOAD
# ==========================================

class UploadLesson(StatesGroup):
    title = State()
    material = State()


class GroupManageCB(CallbackData, prefix="g_man"):
    group_id: int
    action: str


# ==========================================
# STUDENT LESSON VIEW
# ==========================================

class StudentGroupCB(CallbackData, prefix="st_grp"):
    group_id: int


class LessonCB(CallbackData, prefix="st_les"):
    lesson_id: int


# ==========================================
# ADMIN GROUP CREATE / MANAGE
# ==========================================

class CreateGroup(StatesGroup):
    name = State()
    language = State()
    capacity = State()
    link = State()
    teacher = State()


class AssignTeacherCB(CallbackData, prefix="ass_tch"):
    teacher_id: int


# ==========================================
# TEACHER RESULT ENTRY
# ==========================================

class ResultEntry(StatesGroup):
    title = State()
    score = State()
    comment = State()


class TeacherGroupCB(CallbackData, prefix="t_grp"):
    group_id: int
    action: str


class TeacherStudentCB(CallbackData, prefix="t_st"):
    group_id: int
    student_id: int
    action: str


# ==========================================
# KICK REQUEST
# ==========================================

class KickRequestState(StatesGroup):
    reason = State()


class KickApproveCB(CallbackData, prefix="kick_app"):
    request_id: int


class KickRejectCB(CallbackData, prefix="kick_rej"):
    request_id: int


# ==========================================
# OLD ADMIN MANAGEMENT
# Hozircha compatibility uchun qoldiramiz.
# Keyin Staff Management ichiga ko'chiramiz.
# ==========================================

class AddAdminState(StatesGroup):
    telegram_id = State()
    full_name = State()


class RemoveAdminCB(CallbackData, prefix="rm_admin"):
    telegram_id: int


# ==========================================
# NEW STAFF MANAGEMENT
# Superadmin: admin/accountant/superadmin/user role beradi
# ==========================================

class StaffListCB(CallbackData, prefix="stf_lst"):
    role: str
    page: int


class StaffUserCB(CallbackData, prefix="stf_usr"):
    telegram_id: int


class StaffRoleCB(CallbackData, prefix="stf_role"):
    telegram_id: int
    role: str


class StaffRemoveRoleCB(CallbackData, prefix="stf_rm"):
    telegram_id: int


class StaffManualRoleState(StatesGroup):
    telegram_id = State()
    full_name = State()
    role = State()


class StaffManualRoleCB(CallbackData, prefix="stf_mr"):
    role: str


# ==========================================
# ACCOUNTING / PAYMENT PANEL
# accountant/admin/superadmin paymentlar bilan ishlaydi
# ==========================================

class AccountingListCB(CallbackData, prefix="acc_lst"):
    status: str        # pending / approved / rejected / all
    method: str        # cash / card / all
    page: int


class AccountingPaymentCB(CallbackData, prefix="acc_pay"):
    payment_id: int
    action: str        # detail / approve / reject / receipt


class AccountingAssignGroupCB(CallbackData, prefix="acc_grp"):
    payment_id: int
    group_id: int


class AccountingRejectState(StatesGroup):
    reason = State()


class AccountingExportCB(CallbackData, prefix="acc_exp"):
    report_type: str   # today / month / pending / approved / rejected / all