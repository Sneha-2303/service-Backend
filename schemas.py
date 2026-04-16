from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    mobile: str
    full_name: str
    password: str
    role: str = "user"

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) > 72:
            raise ValueError("Password must be max 72 characters")
        return v

class UserLogin(BaseModel):
    username: str   # can be username OR email
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    mobile: str
    full_name: Optional[str]
    role: str
    permissions: Optional[str]
    is_active: bool
    created_at: datetime

class UserLoginResponse(BaseModel):
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    permissions: Optional[str]

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserLoginResponse

# Customer Schemas
class CustomerCreate(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    mobile: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    village: Optional[str] = None
    state_id: int
    district_id: int
    taluka_id: int
    pincode: Optional[str] = None

class CustomerResponse(BaseModel):
    id: int
    first_name: str
    middle_name: Optional[str]
    last_name: str
    full_name: str
    mobile: str
    email: Optional[str]
    address: Optional[str]
    village: Optional[str]
    state: str
    district: str
    taluka: str
    pincode: Optional[str]
    created_at: datetime

# Dealer Schemas
class DealerCreate(BaseModel):
    name: str
    code: str
    contact_person: str
    mobile: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    state_id: int
    district_id: int
    taluka_id: int

class DealerResponse(BaseModel):
    id: int
    name: str
    code: str
    contact_person: str
    mobile: str
    email: Optional[str]
    address: Optional[str]
    state: str
    district: str
    taluka: str
    status: str
    created_at: datetime

# Machine Schemas
class MachineCreate(BaseModel):
    name: str
    description: str
    photo: Optional[str] = None

class MachineResponse(BaseModel):
    id: int
    name: str
    description: str
    photo: Optional[str]
    created_at: datetime

class MachineModelCreate(BaseModel):
    model_name: str
    serial_no: Optional[str] = None
    machine_id: int

class MachineModelResponse(BaseModel):
    id: int
    model_name: str
    serial_no: Optional[str]
    machine_id: int
    machine_name: str

# Complaint Schemas
class ComplaintCreate(BaseModel):
    customer_id: int
    machine_id: int
    machine_model_id: Optional[int] = None
    category_id: int
    subcategory_id: int
    issue_id: Optional[int] = None
    problem_description: str
    installation_date: Optional[datetime] = None

class ComplaintResponse(BaseModel):
    id: int
    complaint_id: str
    customer_name: str
    customer_mobile: str
    machine_name: str
    machine_model: Optional[str]
    problem_description: str
    status: str
    assigned_to: Optional[str]
    installation_date: Optional[datetime]
    warranty_date: Optional[datetime]
    complaint_date: datetime
    resolved_date: Optional[datetime]
    otp: Optional[str]

# Complaint Category Schemas
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class SubCategoryCreate(BaseModel):
    name: str
    category_id: int

class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subcategory_id: int

# Location Schemas
class StateCreate(BaseModel):
    name: str
    code: str

class DistrictCreate(BaseModel):
    name: str
    code: str
    state_id: int

class TalukaCreate(BaseModel):
    name: str
    district_id: int

# Attendance Schemas
class AttendanceCreate(BaseModel):
    user_id: int
    punch_in: datetime
    punch_in_location: Optional[str] = None

class AttendanceUpdate(BaseModel):
    punch_out: datetime
    punch_out_location: Optional[str] = None

# Review Schemas
class ReviewCreate(BaseModel):
    complaint_id: int
    rating: int
    review_text: Optional[str] = None

# Slider Schemas
class SliderCreate(BaseModel):
    title: str
    image_url: str
    link_url: str
    order: Optional[int] = 0

# Media Schemas
class MediaCreate(BaseModel):
    title: str
    video_url: str
    thumbnail_url: Optional[str] = None
    category: str
    machine_id: Optional[int] = None

# User Manual Schemas
class UserManualCreate(BaseModel):
    title: str
    file_url: str
    machine_id: Optional[int] = None
    machine_model_id: Optional[int] = None

# Customer Machine Schemas
class CustomerMachineCreate(BaseModel):
    customer_id: int
    machine_id: int
    machine_model_id: Optional[int] = None
    serial_no: str
    pump_serial_no: Optional[str] = None
    gear_box_serial_no: Optional[str] = None
    installation_date: datetime
    service_engineer_id: Optional[int] = None
    dealer_id: Optional[int] = None