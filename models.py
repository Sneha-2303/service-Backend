from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String)
    email = Column(String)
    mobile = Column(String)

    full_name = Column(String)
    hashed_password = Column(String)

    role = Column(String)

    permissions = Column(String)
    refresh_token = Column(String)
    is_active = Column(Boolean, default=True, server_default="true")
    
    # Service Engineer specific fields (or general profile)
    address = Column(String, nullable=True)
    state = Column(String, nullable=True)
    district = Column(String, nullable=True)
    taluka = Column(String, nullable=True)
    is_team_lead = Column(Boolean, default=False)
    is_under_dealer = Column(Boolean, default=False)
    status = Column(String, default="Active") # Active, Inactive

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Location Models
class State(Base):
    __tablename__ = "states"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"))

class Taluka(Base):
    __tablename__ = "talukas"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    status = Column(String, default="Active")
    district_id = Column(Integer, ForeignKey("districts.id"))
    created_at = Column(DateTime, server_default=func.now())

class Village(Base):
    __tablename__ = "villages"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    taluka_id = Column(Integer, ForeignKey("talukas.id"))

# Machine Models
class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    image_url = Column(String, nullable=True)
    photo = Column(Text, nullable=True) # For base64 or URL

class MachineModel(Base):
    __tablename__ = "machine_models"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String)
    serial_no = Column(String, nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))

# Customer Model
class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    first_name = Column(String)
    middle_name = Column(String, nullable=True)
    last_name = Column(String)
    address = Column(String, nullable=True)
    village = Column(String, nullable=True)
    taluka_id = Column(Integer, ForeignKey("talukas.id"))
    district_id = Column(Integer, ForeignKey("districts.id"))
    state_id = Column(Integer, ForeignKey("states.id"))
    pincode = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# Dealer Model
class Dealer(Base):
    __tablename__ = "dealers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, unique=True)
    contact_person = Column(String)
    mobile = Column(String)
    email = Column(String)
    address = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"))
    district_id = Column(Integer, ForeignKey("districts.id"))
    taluka_id = Column(Integer, ForeignKey("talukas.id"))
    status = Column(String, default="Active")
    created_at = Column(DateTime, server_default=func.now())

# Complaint Models
class ComplaintCategory(Base):
    __tablename__ = "complaint_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    status = Column(String, default="Active")
    created_at = Column(DateTime, server_default=func.now())

class ComplaintSubCategory(Base):
    __tablename__ = "complaint_subcategories"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    status = Column(String, default="Active")
    category_id = Column(Integer, ForeignKey("complaint_categories.id"))

class ComplaintIssue(Base):
    __tablename__ = "complaint_issues"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    subcategory_id = Column(Integer, ForeignKey("complaint_subcategories.id"))

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("complaint_categories.id"))
    subcategory_id = Column(Integer, ForeignKey("complaint_subcategories.id"))
    issue_id = Column(Integer, ForeignKey("complaint_issues.id"), nullable=True)
    problem_description = Column(Text)
    status = Column(String, default="Pending")  # Pending, Assigned, In Progress, Resolved, Closed
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    installation_date = Column(DateTime, nullable=True)
    warranty_date = Column(DateTime, nullable=True)
    complaint_date = Column(DateTime, server_default=func.now())
    resolved_date = Column(DateTime, nullable=True)
    otp = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Customer Machine Assignment
class CustomerMachine(Base):
    __tablename__ = "customer_machines"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    machine_id = Column(Integer, ForeignKey("machines.id"))
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"))
    serial_no = Column(String)
    pump_serial_no = Column(String, nullable=True)
    gear_box_serial_no = Column(String, nullable=True)
    installation_date = Column(DateTime)
    warranty_until = Column(DateTime)
    service_engineer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=True)
    status = Column(String, default="Active")
    created_at = Column(DateTime, server_default=func.now())

# Service Engineer Team
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    team_lead_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, server_default=func.now())

# Attendance
class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, server_default=func.now())
    punch_in = Column(DateTime)
    punch_out = Column(DateTime, nullable=True)
    punch_in_location = Column(String, nullable=True)
    punch_out_location = Column(String, nullable=True)
    hours_worked = Column(Float, default=0)
    status = Column(String, default="Present")  # Present, Absent, Late, Half Day

# Reviews
class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    rating = Column(Integer)  # 1-5
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# Sliders (Mobile Setting)
class Slider(Base):
    __tablename__ = "sliders"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    image_url = Column(String)
    link_url = Column(String)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# Media (Videos)
class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    video_url = Column(String)
    thumbnail_url = Column(String, nullable=True)
    category = Column(String)  # Common, Product Demo, Maintenance, etc.
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

# User Manuals
class UserManual(Base):
    __tablename__ = "user_manuals"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    file_url = Column(String)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"), nullable=True)
    file_size = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
# Machine Parts
class Part(Base):
    __tablename__ = "parts"
    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String)
    part_number = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    photo_url = Column(String, nullable=True)
    photo = Column(Text, nullable=True) # For base64 or URL
    price = Column(String, nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    machine_model_id = Column(Integer, ForeignKey("machine_models.id"), nullable=True)
    status = Column(String, default="Active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# API Logs
class APILog(Base):
    __tablename__ = "api_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    role = Column(String, nullable=True)
    endpoint = Column(String)
    method = Column(String)
    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)
    status_code = Column(Integer)
    status = Column(String)
    error_message = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    labour_charge = Column(Float, default=0.0)
    local_part_amt = Column(Float, default=0.0)
    part_amt = Column(Float, default=0.0)
    total_amt = Column(Float, default=0.0)
    root_cause = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

# CheckSheets
class CheckSheet(Base):
    __tablename__ = "checksheets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    status = Column(String, default="Active")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    sections = relationship("CheckSheetSection", back_populates="checksheet", cascade="all, delete-orphan")

class CheckSheetSection(Base):
    __tablename__ = "checksheet_sections"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    checksheet_id = Column(Integer, ForeignKey("checksheets.id"))
    
    checksheet = relationship("CheckSheet", back_populates="sections")
    items = relationship("CheckSheetItem", back_populates="section", cascade="all, delete-orphan")

class CheckSheetItem(Base):
    __tablename__ = "checksheet_items"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    is_required = Column(Boolean, default=True)
    section_id = Column(Integer, ForeignKey("checksheet_sections.id"))
    
    section = relationship("CheckSheetSection", back_populates="items")
