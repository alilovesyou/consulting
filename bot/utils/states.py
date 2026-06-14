# utils/states.py
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.callback_data import CallbackData

class Registration(StatesGroup):
    fio = State()       
    phone = State()     
    region = State()    
    age = State()     

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