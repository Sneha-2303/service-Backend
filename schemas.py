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

    class Config:
        from_attributes = True

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
    state_id: Optional[int] = None
    district_id: Optional[int] = None
    taluka_id: Optional[int] = None
    state_name: Optional[str] = None
    district_name: Optional[str] = None
    taluka_name: Optional[str] = None
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
    state_id: Optional[int] = None
    district_id: Optional[int] = None
    taluka_id: Optional[int] = None
    state_name: Optional[str] = None
    district_name: Optional[str] = None
    taluka_name: Optional[str] = None

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
    description: Optional[str] = None
    image_url: Optional[str] = None
    photo: Optional[str] = None

class MachineResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    photo: Optional[str] = None
    class Config:
        from_attributes = True

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
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
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
    status: Optional[str] = "Active"

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class SubCategoryCreate(BaseModel):
    name: str
    category_id: int
    status: Optional[str] = "Active"

class SubCategoryResponse(BaseModel):
    id: int
    name: str
    category_id: int
    status: str

    class Config:
        from_attributes = True

class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subcategory_id: int

# Location Schemas
class StateCreate(BaseModel):
    name: str

class StateResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class DistrictCreate(BaseModel):
    name: str
    state_id: int

class DistrictResponse(BaseModel):
    id: int
    name: str
    state_id: int
    class Config:
        from_attributes = True

class TalukaCreate(BaseModel):
    name: str
    district_id: int
    code: Optional[str] = None
    pincode: Optional[str] = None
    status: Optional[str] = "Active"

class TalukaUpdate(BaseModel):
    name: Optional[str] = None
    district_id: Optional[int] = None
    code: Optional[str] = None
    pincode: Optional[str] = None
    status: Optional[str] = None

class TalukaResponse(BaseModel):
    id: int
    name: str
    district_id: int
    code: Optional[str]
    pincode: Optional[str]
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class TalukaFullResponse(TalukaResponse):
    district_name: str
    state_name: str
    zone: Optional[str] = None

class VillageCreate(BaseModel):
    name: str
    taluka_id: int

class VillageUpdate(BaseModel):
    name: Optional[str] = None
    taluka_id: Optional[int] = None

class VillageResponse(BaseModel):
    id: int
    name: str
    taluka_id: int
    class Config:
        from_attributes = True

# Hierarchical Schemas
class TalukaHierarchy(BaseModel):
    id: int
    name: str

class DistrictHierarchy(BaseModel):
    id: int
    name: str
    talukas: List[TalukaHierarchy] = []

class StateHierarchy(BaseModel):
    id: int
    name: str
    districts: List[DistrictHierarchy] = []

# Attendance Schemas
class AttendanceCreate(BaseModel):
    user_id: int
    punch_in: datetime
    punch_in_location: Optional[str] = None

class AttendanceUpdate(BaseModel):
    user_id: Optional[int] = None
    punch_out: datetime
    punch_out_location: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    date: datetime
    punch_in: Optional[datetime]
    punch_out: Optional[datetime]
    punch_in_location: Optional[str]
    punch_out_location: Optional[str]
    hours_worked: float
    activities: int = 0

    class Config:
        from_attributes = True

class MonthlyAttendanceResponse(BaseModel):
    user_id: int
    name: str
    total_days: int
    present_days: int
    absent_days: int
    total_hours: float
    avg_hours_per_day: float
    activities: int
    month: str
    year: int

    class Config:
        from_attributes = True

# Review Schemas
class ReviewCreate(BaseModel):
    complaint_id: int
    rating: int
    review_text: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    complaint_id: str
    customer_name: str
    service_engineer_name: str
    rating: int
    review_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

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
    status: Optional[str] = "Active"

# Service Engineer Schemas
class ServiceEngineerCreate(BaseModel):
    username: str
    email: EmailStr
    mobile: str
    full_name: str
    address: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    is_team_lead: Optional[bool] = False
    is_under_dealer: Optional[bool] = False
    status: Optional[str] = "Active"

class ServiceEngineerResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    mobile: str
    full_name: Optional[str]
    address: Optional[str]
    state: Optional[str]
    district: Optional[str]
    taluka: Optional[str]
    is_team_lead: bool
    is_under_dealer: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Team Schemas
class TeamCreate(BaseModel):
    name: str
    team_lead_id: int
    member_ids: List[int] = []

class TeamResponse(BaseModel):
    id: int
    name: str
    team_lead_id: int
    team_lead_name: str
    created_at: datetime
    members: List[UserResponse] = []

    class Config:
        from_attributes = True
# Part Schemas
class PartCreate(BaseModel):
    part_name: str
    part_number: str
    description: Optional[str] = None
    photo_url: Optional[str] = None
    photo: Optional[str] = None
    price: Optional[str] = None
    machine_id: Optional[int] = None
    machine_model_id: Optional[int] = None
    status: Optional[str] = 'Active'

class PartUpdate(BaseModel):
    part_name: Optional[str] = None
    part_number: Optional[str] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None
    photo: Optional[str] = None
    price: Optional[str] = None
    machine_id: Optional[int] = None
    machine_model_id: Optional[int] = None
    status: Optional[str] = None

class PartResponse(BaseModel):
    id: int
    part_name: str
    part_number: str
    description: Optional[str]
    photo_url: Optional[str]
    photo: Optional[str]
    price: Optional[str]
    machine_id: Optional[int]
    machine_model_id: Optional[int]
    machine_name: Optional[str]
    machine_model_name: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Collection Schemas
class CollectionCreate(BaseModel):
    complaint_id: int
    labour_charge: Optional[float] = 0.0
    local_part_amt: Optional[float] = 0.0
    part_amt: Optional[float] = 0.0
    total_amt: Optional[float] = 0.0
    root_cause: Optional[str] = None

class CollectionResponse(BaseModel):
    id: int
    ticket_id: str
    customer_name: str
    customer_mobile: str
    se_name: str
    warranty: str
    labour_charge: float
    local_part_amt: float
    part_amt: float
    total_amt: float
    date: str
    root_cause: str

    class Config:
        from_attributes = True

# Report Schemas
class DealerReportResponse(BaseModel):
    id: int
    dealer_name: str
    taluka_region: str
    asm_rm_name: str
    service_engineers: List[str]
    uw_visit: int
    gw_visit: int
    ow_visit: int
    total_visits: int
    labour_charge: float
    spare_parts: float
    total_collection: float
    complaint_ids: List[str]
    description: str
    customer_name: str

class PocketReportResponse(BaseModel):
    id: int
    sr_no: int
    dealer_name: str
    asm_name: str
    pocket: str
    service_engg_name: str
    location: str
    open_complaints: int
    mtd_closed: int
    complaint_assigned: int
    complaint_closed_on: int
    date: str

# CheckSheet Schemas
class CheckSheetItemBase(BaseModel):
    description: str
    is_required: bool = True

class CheckSheetItemCreate(CheckSheetItemBase):
    pass

class CheckSheetItemResponse(CheckSheetItemBase):
    id: int
    class Config:
        from_attributes = True

class CheckSheetSectionBase(BaseModel):
    name: str

class CheckSheetSectionCreate(CheckSheetSectionBase):
    items: List[CheckSheetItemCreate] = []

class CheckSheetSectionResponse(CheckSheetSectionBase):
    id: int
    items: List[CheckSheetItemResponse] = []
    class Config:
        from_attributes = True

class CheckSheetBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "Active"

class CheckSheetCreate(CheckSheetBase):
    sections: List[CheckSheetSectionCreate] = []

class CheckSheetResponse(CheckSheetBase):
    id: int
    created_at: datetime
    updated_at: datetime
    sections: List[CheckSheetSectionResponse] = []
    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_customers: int
    total_complaints: int
    today_complaints: int
    assigned_to_engineer: int
    need_installation: int
    hold_complaints: int
    closed_complaints: int
