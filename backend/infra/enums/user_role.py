# [file] enums/user_role.py
# [description] 사용자 권한 분리 
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"
