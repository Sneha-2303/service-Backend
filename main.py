from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from database import Base, engine, get_db
import models, schemas
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
    admin_only,
    validate_password
)

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MITRA Dashboard API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROOT ====================
@app.get("/")
def root():
    return {"message": "MITRA API is running", "status": "healthy"}

# ==================== AUTHENTICATION ====================
@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) |
        (models.User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        username=user.username,
        email=user.email,
        mobile=user.mobile,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        role=user.role
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) |
        (models.User.email == user.username)
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = create_access_token({"sub": db_user.username})

    return {"access_token": token}

@app.get("/users/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "permissions": current_user.permissions,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

# ==================== USER MANAGEMENT ====================
@app.get("/admin/users")
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(admin_only)):
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "mobile": u.mobile,
            "full_name": u.full_name,
            "role": u.role,
            "permissions": u.permissions,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in users
    ]

@app.post("/users")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(admin_only)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    validate_password(user.password)
    hashed_password = get_password_hash(user.password)
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        mobile=user.mobile,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User created successfully", "user_id": new_user.id}

@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: dict, db: Session = Depends(get_db), current_user: models.User = Depends(admin_only)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.items():
        if value is not None:
            setattr(user, key, value)
    
    db.commit()
    return {"message": "User updated successfully"}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(admin_only)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# ==================== CUSTOMER MANAGEMENT ====================
@app.get("/customers")
def get_customers(db: Session = Depends(get_db)):
    customers = db.query(models.Customer).all()
    result = []
    for c in customers:
        cust_user = db.query(models.User).filter(models.User.id == c.user_id).first() if c.user_id else None
        full_name = " ".join(p for p in [c.first_name, c.middle_name or "", c.last_name] if p).strip()
        result.append({
            "id": c.id,
            "first_name": c.first_name,
            "middle_name": c.middle_name,
            "last_name": c.last_name,
            "full_name": full_name,
            "mobile": cust_user.mobile if cust_user else None,
            "email": cust_user.email if cust_user else None,
            "address": c.address,
            "village": c.village,
            "created_at": c.created_at
        })
    return result

@app.post("/customers")
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    # Create user account first
    username = f"{customer.first_name.lower()}_{customer.last_name.lower()}"
    hashed_password = get_password_hash(customer.mobile)
    
    user = models.User(
        username=username,
        email=customer.email,
        mobile=customer.mobile,
        full_name=f"{customer.first_name} {customer.middle_name or ''} {customer.last_name}".strip(),
        hashed_password=hashed_password,
        role="customer"
    )
    db.add(user)
    db.flush()
    
    new_customer = models.Customer(
        user_id=user.id,
        first_name=customer.first_name,
        middle_name=customer.middle_name,
        last_name=customer.last_name,
        address=customer.address,
        village=customer.village,
        state_id=customer.state_id,
        district_id=customer.district_id,
        taluka_id=customer.taluka_id,
        pincode=customer.pincode
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return {"message": "Customer created successfully", "customer_id": new_customer.id}

# ==================== DEALER MANAGEMENT ====================
@app.get("/dealers")
def get_dealers(db: Session = Depends(get_db)):
    dealers = db.query(models.Dealer).all()
    return dealers

@app.post("/dealers")
def create_dealer(dealer: schemas.DealerCreate, db: Session = Depends(get_db)):
    new_dealer = models.Dealer(
        name=dealer.name,
        code=dealer.code,
        contact_person=dealer.contact_person,
        mobile=dealer.mobile,
        email=dealer.email,
        address=dealer.address,
        state_id=dealer.state_id,
        district_id=dealer.district_id,
        taluka_id=dealer.taluka_id
    )
    db.add(new_dealer)
    db.commit()
    db.refresh(new_dealer)
    return {"message": "Dealer created successfully", "dealer_id": new_dealer.id}

@app.put("/dealers/{dealer_id}")
def update_dealer(dealer_id: int, dealer_data: dict, db: Session = Depends(get_db)):
    dealer = db.query(models.Dealer).filter(models.Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    for key, value in dealer_data.items():
        if value is not None:
            setattr(dealer, key, value)
    
    db.commit()
    return {"message": "Dealer updated successfully"}

@app.delete("/dealers/{dealer_id}")
def delete_dealer(dealer_id: int, db: Session = Depends(get_db)):
    dealer = db.query(models.Dealer).filter(models.Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    db.delete(dealer)
    db.commit()
    return {"message": "Dealer deleted successfully"}

# ==================== MACHINE MANAGEMENT ====================
@app.get("/machines")
def get_machines(db: Session = Depends(get_db)):
    return db.query(models.Machine).all()

@app.post("/machines")
def create_machine(machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    new_machine = models.Machine(
        name=machine.name,
        description=machine.description,
        photo=machine.photo
    )
    db.add(new_machine)
    db.commit()
    db.refresh(new_machine)
    return new_machine

@app.put("/machines/{machine_id}")
def update_machine(machine_id: int, machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    db_machine.name = machine.name
    db_machine.description = machine.description
    db_machine.photo = machine.photo
    db.commit()
    db.refresh(db_machine)
    return db_machine

@app.delete("/machines/{machine_id}")
def delete_machine(machine_id: int, db: Session = Depends(get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    db.delete(machine)
    db.commit()
    return {"message": "Machine deleted"}

# ==================== MACHINE MODELS ====================
@app.get("/machines/{machine_id}/models")
def get_machine_models(machine_id: int, db: Session = Depends(get_db)):
    return db.query(models.MachineModel).filter(models.MachineModel.machine_id == machine_id).all()

@app.post("/models")
def create_model(model: schemas.MachineModelCreate, db: Session = Depends(get_db)):
    new_model = models.MachineModel(
        model_name=model.model_name,
        serial_no=model.serial_no,
        machine_id=model.machine_id
    )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return new_model

# ==================== COMPLAINT MANAGEMENT ====================
@app.get("/complaints")
def get_complaints(db: Session = Depends(get_db)):
    complaints = db.query(models.Complaint).all()
    result = []
    for c in complaints:
        customer = db.query(models.Customer).filter(models.Customer.id == c.customer_id).first() if c.customer_id else None
        cust_user = db.query(models.User).filter(models.User.id == customer.user_id).first() if customer and customer.user_id else None
        machine = db.query(models.Machine).filter(models.Machine.id == c.machine_id).first() if c.machine_id else None
        assigned = db.query(models.User).filter(models.User.id == c.assigned_to).first() if c.assigned_to else None
        result.append({
            "id": c.id,
            "complaint_id": c.complaint_id,
            "customer_name": cust_user.full_name if cust_user else None,
            "customer_mobile": cust_user.mobile if cust_user else None,
            "machine_name": machine.name if machine else None,
            "problem_description": c.problem_description,
            "status": c.status,
            "assigned_to": assigned.full_name if assigned else None,
            "complaint_date": c.complaint_date,
            "installation_date": c.installation_date,
            "warranty_date": c.warranty_date
        })
    return result

@app.post("/complaints")
def create_complaint(complaint: schemas.ComplaintCreate, db: Session = Depends(get_db)):
    complaint_id = f"SR-{datetime.now().strftime('%y')}-{str(uuid.uuid4().int)[:6]}"
    
    new_complaint = models.Complaint(
        complaint_id=complaint_id,
        customer_id=complaint.customer_id,
        machine_id=complaint.machine_id,
        machine_model_id=complaint.machine_model_id,
        category_id=complaint.category_id,
        subcategory_id=complaint.subcategory_id,
        issue_id=complaint.issue_id,
        problem_description=complaint.problem_description,
        installation_date=complaint.installation_date,
        warranty_date=complaint.installation_date + timedelta(days=365) if complaint.installation_date else None,
        otp=str(uuid.uuid4().int)[:6]
    )
    
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return {"message": "Complaint created successfully", "complaint_id": new_complaint.complaint_id}

@app.put("/complaints/{complaint_id}/status")
def update_complaint_status(complaint_id: int, status: str, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = status
    if status == "Resolved":
        complaint.resolved_date = datetime.now()
    
    db.commit()
    return {"message": f"Complaint status updated to {status}"}

# ==================== LOCATION APIs ====================
@app.get("/states")
def get_states(db: Session = Depends(get_db)):
    return db.query(models.State).all()

@app.post("/states")
def create_state(state: schemas.StateCreate, db: Session = Depends(get_db)):
    new_state = models.State(name=state.name, code=state.code)
    db.add(new_state)
    db.commit()
    db.refresh(new_state)
    return new_state

@app.get("/districts/{state_id}")
def get_districts(state_id: int, db: Session = Depends(get_db)):
    return db.query(models.District).filter(models.District.state_id == state_id).all()

@app.post("/districts")
def create_district(district: schemas.DistrictCreate, db: Session = Depends(get_db)):
    new_district = models.District(name=district.name, code=district.code, state_id=district.state_id)
    db.add(new_district)
    db.commit()
    db.refresh(new_district)
    return new_district

@app.get("/talukas/{district_id}")
def get_talukas(district_id: int, db: Session = Depends(get_db)):
    return db.query(models.Taluka).filter(models.Taluka.district_id == district_id).all()

@app.post("/talukas")
def create_taluka(taluka: schemas.TalukaCreate, db: Session = Depends(get_db)):
    new_taluka = models.Taluka(name=taluka.name, district_id=taluka.district_id)
    db.add(new_taluka)
    db.commit()
    db.refresh(new_taluka)
    return new_taluka

# ==================== DASHBOARD STATS ====================
@app.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_customers = db.query(models.Customer).count()
    total_complaints = db.query(models.Complaint).count()
    pending_complaints = db.query(models.Complaint).filter(models.Complaint.status == "Pending").count()
    resolved_complaints = db.query(models.Complaint).filter(models.Complaint.status == "Resolved").count()
    total_machines = db.query(models.Machine).count()
    total_dealers = db.query(models.Dealer).count()
    total_engineers = db.query(models.User).filter(models.User.role == "service_engineer").count()
    
    return {
        "total_customers": total_customers,
        "total_complaints": total_complaints,
        "pending_complaints": pending_complaints,
        "resolved_complaints": resolved_complaints,
        "total_machines": total_machines,
        "total_dealers": total_dealers,
        "total_engineers": total_engineers
    }

# ==================== COMPLAINT CATEGORIES ====================
@app.get("/complaint-categories")
def get_complaint_categories(db: Session = Depends(get_db)):
    return db.query(models.ComplaintCategory).all()

@app.post("/complaint-categories")
def create_complaint_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    new_category = models.ComplaintCategory(name=category.name, description=category.description)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.get("/complaint-subcategories/{category_id}")
def get_complaint_subcategories(category_id: int, db: Session = Depends(get_db)):
    return db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.category_id == category_id).all()

@app.post("/complaint-subcategories")
def create_complaint_subcategory(subcategory: schemas.SubCategoryCreate, db: Session = Depends(get_db)):
    new_subcategory = models.ComplaintSubCategory(name=subcategory.name, category_id=subcategory.category_id)
    db.add(new_subcategory)
    db.commit()
    db.refresh(new_subcategory)
    return new_subcategory

# ==================== ATTENDANCE ====================
@app.post("/attendance/punch-in")
def punch_in(attendance: schemas.AttendanceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    today = datetime.now().date()
    existing = db.query(models.Attendance).filter(
        models.Attendance.user_id == current_user.id,
        models.Attendance.date >= datetime.combine(today, datetime.min.time())
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already punched in today")
    
    new_attendance = models.Attendance(
        user_id=current_user.id,
        punch_in=attendance.punch_in,
        punch_in_location=attendance.punch_in_location
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return {"message": "Punch in successful", "attendance_id": new_attendance.id}

@app.put("/attendance/punch-out")
def punch_out(attendance: schemas.AttendanceUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    today = datetime.now().date()
    record = db.query(models.Attendance).filter(
        models.Attendance.user_id == current_user.id,
        models.Attendance.date >= datetime.combine(today, datetime.min.time())
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="No punch in record found")
    
    if record.punch_out:
        raise HTTPException(status_code=400, detail="Already punched out")
    
    record.punch_out = attendance.punch_out
    record.punch_out_location = attendance.punch_out_location
    if record.punch_in:
        hours = (attendance.punch_out - record.punch_in).total_seconds() / 3600
        record.hours_worked = round(hours, 2)
    
    db.commit()
    return {"message": "Punch out successful", "hours_worked": record.hours_worked}

# ==================== SLIDER MANAGEMENT ====================
@app.get("/sliders")
def get_sliders(db: Session = Depends(get_db)):
    return db.query(models.Slider).filter(models.Slider.is_active == True).order_by(models.Slider.order).all()

@app.post("/sliders")
def create_slider(slider: schemas.SliderCreate, db: Session = Depends(get_db)):
    new_slider = models.Slider(
        title=slider.title,
        image_url=slider.image_url,
        link_url=slider.link_url,
        order=slider.order
    )
    db.add(new_slider)
    db.commit()
    db.refresh(new_slider)
    return new_slider

# ==================== MEDIA MANAGEMENT ====================
@app.get("/media")
def get_media(db: Session = Depends(get_db)):
    return db.query(models.Media).filter(models.Media.is_active == True).all()

@app.post("/media")
def create_media(media: schemas.MediaCreate, db: Session = Depends(get_db)):
    new_media = models.Media(
        title=media.title,
        video_url=media.video_url,
        thumbnail_url=media.thumbnail_url,
        category=media.category,
        machine_id=media.machine_id
    )
    db.add(new_media)
    db.commit()
    db.refresh(new_media)
    return new_media

# ==================== USER MANUALS ====================
@app.get("/user-manuals")
def get_user_manuals(db: Session = Depends(get_db)):
    return db.query(models.UserManual).filter(models.UserManual.is_active == True).all()

@app.post("/user-manuals")
def create_user_manual(manual: schemas.UserManualCreate, db: Session = Depends(get_db)):
    new_manual = models.UserManual(
        title=manual.title,
        file_url=manual.file_url,
        machine_id=manual.machine_id,
        machine_model_id=manual.machine_model_id
    )
    db.add(new_manual)
    db.commit()
    db.refresh(new_manual)
    return new_manual

# ==================== REVIEWS ====================
@app.post("/reviews")
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_review = models.Review(
        complaint_id=review.complaint_id,
        customer_id=current_user.id,
        rating=review.rating,
        review_text=review.review_text
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return {"message": "Review submitted successfully"}

# ==================== SERVICE ENGINEERS ====================
@app.get("/service-engineers")
def get_service_engineers(db: Session = Depends(get_db)):
    engineers = db.query(models.User).filter(models.User.role == "service_engineer").all()
    return [{"id": e.id, "full_name": e.full_name, "mobile": e.mobile} for e in engineers]

# ==================== CUSTOMER MACHINE MANAGEMENT ====================
@app.get("/customer-machines")
def get_customer_machines(db: Session = Depends(get_db)):
    cms = db.query(models.CustomerMachine).all()
    result = []
    for cm in cms:
        customer = db.query(models.Customer).filter(models.Customer.id == cm.customer_id).first()
        cust_user = db.query(models.User).filter(models.User.id == customer.user_id).first() if customer and customer.user_id else None
        machine = db.query(models.Machine).filter(models.Machine.id == cm.machine_id).first()
        machine_model = db.query(models.MachineModel).filter(models.MachineModel.id == cm.machine_model_id).first() if cm.machine_model_id else None
        engineer = db.query(models.User).filter(models.User.id == cm.service_engineer_id).first() if cm.service_engineer_id else None
        dealer = db.query(models.Dealer).filter(models.Dealer.id == cm.dealer_id).first() if cm.dealer_id else None

        customer_full_name = ""
        if customer:
            parts = [customer.first_name, customer.middle_name or "", customer.last_name]
            customer_full_name = " ".join(p for p in parts if p).strip()

        result.append({
            "id": cm.id,
            "customer_name": customer_full_name,
            "customer_mobile": cust_user.mobile if cust_user else "",
            "machine_name": machine.name if machine else "",
            "machine_model": machine_model.model_name if machine_model else "",
            "serial_no": cm.serial_no,
            "pump_serial_no": cm.pump_serial_no or "",
            "gear_box_serial_no": cm.gear_box_serial_no or "",
            "installation_date": cm.installation_date,
            "warranty_until": cm.warranty_until,
            "service_engineer": engineer.full_name if engineer else "",
            "dealer_name": dealer.name if dealer else "",
            "status": "Active"
        })
    return result

@app.post("/customer-machines")
def create_customer_machine(cm: schemas.CustomerMachineCreate, db: Session = Depends(get_db)):
    warranty_until = cm.installation_date + timedelta(days=365)

    new_cm = models.CustomerMachine(
        customer_id=cm.customer_id,
        machine_id=cm.machine_id,
        machine_model_id=cm.machine_model_id,
        serial_no=cm.serial_no,
        pump_serial_no=cm.pump_serial_no,
        gear_box_serial_no=cm.gear_box_serial_no,
        installation_date=cm.installation_date,
        warranty_until=warranty_until,
        service_engineer_id=cm.service_engineer_id,
        dealer_id=cm.dealer_id
    )

    try:
        db.add(new_cm)
        db.commit()
        db.refresh(new_cm)
        return {"message": "Customer machine created successfully", "id": new_cm.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer machine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)