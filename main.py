from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import uuid
import calendar

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

# ==================== DASHBOARD STATS ====================
@app.get("/dashboard/stats", response_model=schemas.DashboardStatsResponse)
def get_dashboard_stats(
    month: Optional[str] = None,
    year: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Base queries
    q_customers = db.query(models.Customer)
    q_complaints = db.query(models.Complaint)
    
    # Helper to apply filters
    def apply_filters(query, model):
        date_field = models.Customer.created_at if model == models.Customer else models.Complaint.complaint_date
        
        if from_date:
            try:
                d = datetime.strptime(from_date, "%Y-%m-%d")
                query = query.filter(date_field >= d)
            except: pass
        if to_date:
            try:
                # Add 23:59:59 to include the whole to_date
                d = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
                query = query.filter(date_field <= d)
            except: pass
        if month and month != "":
            try:
                month_idx = list(calendar.month_name).index(month)
                query = query.filter(extract('month', date_field) == month_idx)
            except: pass
        if year:
            query = query.filter(extract('year', date_field) == year)
            
        return query

    # Apply filters to core queries
    q_customers = apply_filters(q_customers, models.Customer)
    q_complaints = apply_filters(q_complaints, models.Complaint)

    total_customers = q_customers.count()
    total_complaints = q_complaints.count()
    
    # Today's complaints (Always absolute current day)
    today = datetime.now().date()
    today_complaints = db.query(models.Complaint).filter(func.date(models.Complaint.complaint_date) == today).count()
    
    assigned_to_engineer = q_complaints.filter(models.Complaint.status == "Assigned").count()
    need_installation = q_complaints.filter(models.Complaint.status == "Need Installation").count()
    hold_complaints = q_complaints.filter(models.Complaint.status == "Hold").count()
    closed_complaints = q_complaints.filter(models.Complaint.status.in_(["Closed", "Resolved"])).count()
    
    return {
        "total_customers": total_customers,
        "total_complaints": total_complaints,
        "today_complaints": today_complaints,
        "assigned_to_engineer": assigned_to_engineer,
        "need_installation": need_installation,
        "hold_complaints": hold_complaints,
        "closed_complaints": closed_complaints
    }

@app.get("/dashboard/top-engineers")
def get_top_engineers(db: Session = Depends(get_db)):
    # Fetch real service engineers
    engineers = db.query(models.User).filter(models.User.role == "service_engineer").all()
    
    # In a production app, these would be calculated from complaints and reviews.
    # For this demo, we use the real names with varied stats.
    
    top_mttr = []
    top_rating = []
    
    # Take up to 3 engineers for MTTR
    for i, eng in enumerate(engineers[:3]):
        initials = "".join([n[0] for n in eng.full_name.split()[:2]]).upper() if eng.full_name else "SE"
        top_mttr.append({
            "name": eng.full_name,
            "mttr": 2.5 + i,
            "complaints": 12 - (i * 2),
            "initials": initials
        })
        
    # Take another 3 (or the same if few) for Ratings
    rating_source = engineers[3:6] if len(engineers) >= 6 else engineers
    for i, eng in enumerate(rating_source[:3]):
        initials = "".join([n[0] for n in eng.full_name.split()[:2]]).upper() if eng.full_name else "SE"
        top_rating.append({
            "name": eng.full_name,
            "rating": 5 if i == 0 else 4,
            "complaints": 25 + (i * 10),
            "initials": initials
        })
        
    return {
        "lowest_mttr": top_mttr,
        "highest_rating": top_rating
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
        state = db.query(models.State).filter(models.State.id == c.state_id).first()
        district = db.query(models.District).filter(models.District.id == c.district_id).first()
        taluka = db.query(models.Taluka).filter(models.Taluka.id == c.taluka_id).first()
        
        customer_machine = db.query(models.CustomerMachine).filter(models.CustomerMachine.customer_id == c.id).first()
        machine_name = ""
        machine_model_name = ""
        serial_no = ""
        if customer_machine:
            machine = db.query(models.Machine).filter(models.Machine.id == customer_machine.machine_id).first()
            if machine: machine_name = machine.name
            machine_model = db.query(models.MachineModel).filter(models.MachineModel.id == customer_machine.machine_model_id).first()
            if machine_model: machine_model_name = machine_model.model_name
            serial_no = customer_machine.serial_no or ""

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
            "state": state.name if state else "",
            "district": district.name if district else "",
            "taluka": taluka.name if taluka else "",
            "machine": machine_name,
            "machine_model": machine_model_name,
            "serial_no": serial_no,
            "created_at": c.created_at
        })
    return result

@app.post("/customers")
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    state_id = customer.state_id
    if not state_id and customer.state_name:
        state = db.query(models.State).filter(models.State.name == customer.state_name).first()
        if not state:
            state = models.State(name=customer.state_name)
            db.add(state)
            db.commit()
            db.refresh(state)
        state_id = state.id
        
    district_id = customer.district_id
    if not district_id and customer.district_name and state_id:
        district = db.query(models.District).filter(models.District.name == customer.district_name, models.District.state_id == state_id).first()
        if not district:
            district = models.District(name=customer.district_name, state_id=state_id)
            db.add(district)
            db.commit()
            db.refresh(district)
        district_id = district.id
        
    taluka_id = customer.taluka_id
    if not taluka_id and customer.taluka_name and district_id:
        taluka = db.query(models.Taluka).filter(models.Taluka.name == customer.taluka_name, models.Taluka.district_id == district_id).first()
        if not taluka:
            taluka = models.Taluka(name=customer.taluka_name, district_id=district_id)
            db.add(taluka)
            db.commit()
            db.refresh(taluka)
        taluka_id = taluka.id

    # Validate location fields
    if not state_id:
        raise HTTPException(status_code=400, detail="State is required")
    if not district_id:
        raise HTTPException(status_code=400, detail="District is required")
    if not taluka_id:
        raise HTTPException(status_code=400, detail="Taluka is required")

    # Check for existing mobile/email
    if db.query(models.User).filter(models.User.mobile == customer.mobile).first():
        raise HTTPException(status_code=400, detail="A user with this mobile number already exists")
        
    if customer.email and db.query(models.User).filter(models.User.email == customer.email).first():
        raise HTTPException(status_code=400, detail="A user with this email address already exists")

    try:
        # Create user account first
        base_username = f"{customer.first_name.lower()}_{customer.last_name.lower()}"
        username = base_username
        counter = 1
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1
            
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
            state_id=state_id,
            district_id=district_id,
            taluka_id=taluka_id,
            pincode=customer.pincode
        )
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        return {"message": "Customer created successfully", "customer_id": new_customer.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/customers/{customer_id}")
def update_customer(customer_id: int, customer_data: dict, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update location fields by name if provided
    state_name = customer_data.pop("state", None)
    if state_name:
        state = db.query(models.State).filter(models.State.name == state_name).first()
        if state:
            customer.state_id = state.id
    
    district_name = customer_data.pop("district", None)
    if district_name and customer.state_id:
        district = db.query(models.District).filter(
            models.District.name == district_name, 
            models.District.state_id == customer.state_id
        ).first()
        if district:
            customer.district_id = district.id
            
    taluka_name = customer_data.pop("taluka", None)
    if taluka_name and customer.district_id:
        taluka = db.query(models.Taluka).filter(
            models.Taluka.name == taluka_name, 
            models.Taluka.district_id == customer.district_id
        ).first()
        if taluka:
            customer.taluka_id = taluka.id

    # Update location fields by ID if provided
    if "state_id" in customer_data: customer.state_id = customer_data.pop("state_id")
    if "district_id" in customer_data: customer.district_id = customer_data.pop("district_id")
    if "taluka_id" in customer_data: customer.taluka_id = customer_data.pop("taluka_id")

    # Update customer fields
    for key in ["first_name", "middle_name", "last_name", "address", "village", "pincode"]:
        if key in customer_data and customer_data[key] is not None:
            setattr(customer, key, customer_data[key])
    
    # Update linked user if mobile/email changed
    if customer.user_id:
        user = db.query(models.User).filter(models.User.id == customer.user_id).first()
        if user:
            if "mobile" in customer_data:
                user.mobile = customer_data["mobile"]
            if "email" in customer_data:
                user.email = customer_data["email"]
            full_name = " ".join(p for p in [
                customer_data.get("first_name", customer.first_name),
                customer_data.get("middle_name", customer.middle_name) or "",
                customer_data.get("last_name", customer.last_name)
            ] if p).strip()
            user.full_name = full_name
    
    db.commit()
    return {"message": "Customer updated successfully"}

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted successfully"}

# ==================== DEALER MANAGEMENT ====================
@app.get("/dealers")
def get_dealers(db: Session = Depends(get_db)):
    dealers = db.query(models.Dealer).all()
    result = []
    for d in dealers:
        state = db.query(models.State).filter(models.State.id == d.state_id).first()
        district = db.query(models.District).filter(models.District.id == d.district_id).first()
        taluka = db.query(models.Taluka).filter(models.Taluka.id == d.taluka_id).first()
        
        result.append({
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "contact_person": d.contact_person,
            "mobile": d.mobile,
            "email": d.email,
            "address": d.address,
            "state_id": d.state_id,
            "district_id": d.district_id,
            "taluka_id": d.taluka_id,
            "state": state.name if state else None,
            "districts": [district.name] if district else [],
            "talukas": [taluka.name] if taluka else []
        })
    return result

@app.post("/dealers")
def create_dealer(dealer: schemas.DealerCreate, db: Session = Depends(get_db)):
    state_id = dealer.state_id
    if not state_id and dealer.state_name:
        state = db.query(models.State).filter(models.State.name == dealer.state_name).first()
        if not state:
            state = models.State(name=dealer.state_name)
            db.add(state)
            db.commit()
            db.refresh(state)
        state_id = state.id

    district_id = dealer.district_id
    if not district_id and dealer.district_name and state_id:
        district = db.query(models.District).filter(models.District.name == dealer.district_name, models.District.state_id == state_id).first()
        if not district:
            district = models.District(name=dealer.district_name, state_id=state_id)
            db.add(district)
            db.commit()
            db.refresh(district)
        district_id = district.id

    taluka_id = dealer.taluka_id
    if not taluka_id and dealer.taluka_name and district_id:
        taluka = db.query(models.Taluka).filter(models.Taluka.name == dealer.taluka_name, models.Taluka.district_id == district_id).first()
        if not taluka:
            taluka = models.Taluka(name=dealer.taluka_name, district_id=district_id)
            db.add(taluka)
            db.commit()
            db.refresh(taluka)
        taluka_id = taluka.id

    if state_id and not db.query(models.State).filter(models.State.id == state_id).first():
        raise HTTPException(status_code=400, detail=f"State with ID {state_id} not found")
        
    if district_id and not db.query(models.District).filter(models.District.id == district_id).first():
        raise HTTPException(status_code=400, detail=f"District with ID {district_id} not found")
        
    if taluka_id and not db.query(models.Taluka).filter(models.Taluka.id == taluka_id).first():
        raise HTTPException(status_code=400, detail=f"Taluka with ID {taluka_id} not found")
        
    try:
        new_dealer = models.Dealer(
            name=dealer.name,
            code=dealer.code,
            contact_person=dealer.contact_person,
            mobile=dealer.mobile,
            email=dealer.email,
            address=dealer.address,
            state_id=state_id,
            district_id=district_id,
            taluka_id=taluka_id
        )
        db.add(new_dealer)
        db.commit()
        db.refresh(new_dealer)
        return {"message": "Dealer created successfully", "dealer_id": new_dealer.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/dealers/{dealer_id}")
def update_dealer(dealer_id: int, dealer_data: dict, db: Session = Depends(get_db)):
    dealer = db.query(models.Dealer).filter(models.Dealer.id == dealer_id).first()
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    state_name = dealer_data.pop("state_name", None)
    if state_name:
        state = db.query(models.State).filter(models.State.name == state_name).first()
        if not state:
            state = models.State(name=state_name)
            db.add(state)
            db.commit()
            db.refresh(state)
        dealer.state_id = state.id

    district_name = dealer_data.pop("district_name", None)
    if district_name and dealer.state_id:
        district = db.query(models.District).filter(models.District.name == district_name, models.District.state_id == dealer.state_id).first()
        if not district:
            district = models.District(name=district_name, state_id=dealer.state_id)
            db.add(district)
            db.commit()
            db.refresh(district)
        dealer.district_id = district.id

    taluka_name = dealer_data.pop("taluka_name", None)
    if taluka_name and dealer.district_id:
        taluka = db.query(models.Taluka).filter(models.Taluka.name == taluka_name, models.Taluka.district_id == dealer.district_id).first()
        if not taluka:
            taluka = models.Taluka(name=taluka_name, district_id=dealer.district_id)
            db.add(taluka)
            db.commit()
            db.refresh(taluka)
        dealer.taluka_id = taluka.id

    for key, value in dealer_data.items():
        if value is not None and hasattr(dealer, key):
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

@app.post("/machines", response_model=schemas.MachineResponse)
def create_machine(machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    try:
        new_machine = models.Machine(
            name=machine.name,
            description=machine.description,
            photo=machine.photo
        )
        db.add(new_machine)
        db.commit()
        db.refresh(new_machine)
        return new_machine
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating machine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/machines/{machine_id}", response_model=schemas.MachineResponse)
def update_machine(machine_id: int, machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if not db_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    try:
        db_machine.name = machine.name
        db_machine.description = machine.description
        db_machine.photo = machine.photo
        db.commit()
        db.refresh(db_machine)
        return db_machine
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating machine: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/machine-models", response_model=List[schemas.MachineModelResponse])
def get_all_machine_models(db: Session = Depends(get_db)):
    models_list = db.query(models.MachineModel).all()
    result = []
    for m in models_list:
        machine = db.query(models.Machine).filter(models.Machine.id == m.machine_id).first()
        result.append({
            "id": m.id,
            "model_name": m.model_name,
            "serial_no": m.serial_no,
            "machine_id": m.machine_id,
            "machine_name": machine.name if machine else "Unknown"
        })
    return result

@app.post("/models", response_model=schemas.MachineModelResponse)
def create_model(model: schemas.MachineModelCreate, db: Session = Depends(get_db)):
    try:
        new_model = models.MachineModel(
            model_name=model.model_name,
            serial_no=model.serial_no,
            machine_id=model.machine_id
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        # Return with machine_name
        machine = db.query(models.Machine).filter(models.Machine.id == new_model.machine_id).first()
        return {
            "id": new_model.id,
            "model_name": new_model.model_name,
            "serial_no": new_model.serial_no,
            "machine_id": new_model.machine_id,
            "machine_name": machine.name if machine else "Unknown"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating machine model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/models/{model_id}", response_model=schemas.MachineModelResponse)
def update_machine_model(model_id: int, model: schemas.MachineModelCreate, db: Session = Depends(get_db)):
    db_model = db.query(models.MachineModel).filter(models.MachineModel.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        db_model.model_name = model.model_name
        db_model.serial_no = model.serial_no
        db_model.machine_id = model.machine_id
        db.commit()
        db.refresh(db_model)
        
        machine = db.query(models.Machine).filter(models.Machine.id == db_model.machine_id).first()
        return {
            "id": db_model.id,
            "model_name": db_model.model_name,
            "serial_no": db_model.serial_no,
            "machine_id": db_model.machine_id,
            "machine_name": machine.name if machine else "Unknown"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating machine model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/models/{model_id}")
def delete_machine_model(model_id: int, db: Session = Depends(get_db)):
    db_model = db.query(models.MachineModel).filter(models.MachineModel.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    db.delete(db_model)
    db.commit()
    return {"message": "Model deleted"}

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
    if complaint.customer_id and not db.query(models.Customer).filter(models.Customer.id == complaint.customer_id).first():
        raise HTTPException(status_code=400, detail=f"Customer with ID {complaint.customer_id} not found")
        
    if complaint.machine_id and not db.query(models.Machine).filter(models.Machine.id == complaint.machine_id).first():
        raise HTTPException(status_code=400, detail=f"Machine with ID {complaint.machine_id} not found")
        
    if complaint.category_id and not db.query(models.ComplaintCategory).filter(models.ComplaintCategory.id == complaint.category_id).first():
        raise HTTPException(status_code=400, detail=f"Category with ID {complaint.category_id} not found")
        
    if complaint.subcategory_id and not db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.id == complaint.subcategory_id).first():
        raise HTTPException(status_code=400, detail=f"Subcategory with ID {complaint.subcategory_id} not found")
        
    if complaint.machine_model_id and not db.query(models.MachineModel).filter(models.MachineModel.id == complaint.machine_model_id).first():
        raise HTTPException(status_code=400, detail=f"Machine Model with ID {complaint.machine_model_id} not found")
        
    try:
        complaint_id = f"SR-{datetime.now().strftime('%y')}-{str(uuid.uuid4().int)[:6]}"
        
        new_complaint = models.Complaint(
            complaint_id=complaint_id,
            customer_id=complaint.customer_id,
            machine_id=complaint.machine_id,
            machine_model_id=complaint.machine_model_id,
            category_id=complaint.category_id,
            subcategory_id=complaint.subcategory_id,
            problem_description=complaint.problem_description,
            installation_date=complaint.installation_date,
            warranty_date=complaint.installation_date + timedelta(days=365) if complaint.installation_date else None,
            otp=str(uuid.uuid4().int)[:6]
        )
        
        db.add(new_complaint)
        db.commit()
        db.refresh(new_complaint)
        return {"message": "Complaint created successfully", "complaint_id": new_complaint.complaint_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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

@app.delete("/complaints/{complaint_id}")
def delete_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(models.Complaint).filter(models.Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    try:
        # Delete related collections and reviews to avoid foreign key constraint errors
        db.query(models.Collection).filter(models.Collection.complaint_id == complaint_id).delete(synchronize_session=False)
        db.query(models.Review).filter(models.Review.complaint_id == complaint_id).delete(synchronize_session=False)
        
        db.delete(complaint)
        db.commit()
        return {"message": "Complaint deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete complaint: {str(e)}")


# ==================== COMPLAINT CATEGORY APIs ====================
@app.get("/complaint-categories", response_model=List[schemas.CategoryResponse])
def get_complaint_categories(db: Session = Depends(get_db)):
    return db.query(models.ComplaintCategory).all()

@app.post("/complaint-categories", response_model=schemas.CategoryResponse)
def create_complaint_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(models.ComplaintCategory).filter(models.ComplaintCategory.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    new_category = models.ComplaintCategory(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

@app.put("/complaint-categories/{category_id}", response_model=schemas.CategoryResponse)
def update_complaint_category(category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(models.ComplaintCategory).filter(models.ComplaintCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    for key, value in category.dict().items():
        setattr(db_category, key, value)
        
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/complaint-categories/{category_id}")
def delete_complaint_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.ComplaintCategory).filter(models.ComplaintCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}

# ==================== COMPLAINT SUBCATEGORY APIs ====================
@app.get("/complaint-subcategories", response_model=List[schemas.SubCategoryResponse])
def get_complaint_subcategories(db: Session = Depends(get_db)):
    return db.query(models.ComplaintSubCategory).all()

@app.get("/complaint-subcategories/category/{category_id}", response_model=List[schemas.SubCategoryResponse])
def get_subcategories_by_category(category_id: int, db: Session = Depends(get_db)):
    return db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.category_id == category_id).all()

@app.post("/complaint-subcategories", response_model=schemas.SubCategoryResponse)
def create_complaint_subcategory(subcategory: schemas.SubCategoryCreate, db: Session = Depends(get_db)):
    # Validate category exists
    if not db.query(models.ComplaintCategory).filter(models.ComplaintCategory.id == subcategory.category_id).first():
        raise HTTPException(status_code=400, detail=f"Category with ID {subcategory.category_id} not found")
        
    new_subcategory = models.ComplaintSubCategory(**subcategory.dict())
    db.add(new_subcategory)
    db.commit()
    db.refresh(new_subcategory)
    return new_subcategory

@app.put("/complaint-subcategories/{subcategory_id}", response_model=schemas.SubCategoryResponse)
def update_complaint_subcategory(subcategory_id: int, subcategory: schemas.SubCategoryCreate, db: Session = Depends(get_db)):
    db_subcategory = db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.id == subcategory_id).first()
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
        
    if not db.query(models.ComplaintCategory).filter(models.ComplaintCategory.id == subcategory.category_id).first():
        raise HTTPException(status_code=400, detail=f"Category with ID {subcategory.category_id} not found")
        
    for key, value in subcategory.dict().items():
        setattr(db_subcategory, key, value)
        
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory

@app.delete("/complaint-subcategories/{subcategory_id}")
def delete_complaint_subcategory(subcategory_id: int, db: Session = Depends(get_db)):
    db_subcategory = db.query(models.ComplaintSubCategory).filter(models.ComplaintSubCategory.id == subcategory_id).first()
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")
        
    db.delete(db_subcategory)
    db.commit()
    return {"message": "Subcategory deleted successfully"}
# ==================== PART MANAGEMENT ====================
@app.get("/parts", response_model=List[schemas.PartResponse])
def get_parts(db: Session = Depends(get_db)):
    parts = db.query(models.Part).all()
    result = []
    for p in parts:
        machine = db.query(models.Machine).filter(models.Machine.id == p.machine_id).first() if p.machine_id else None
        model = db.query(models.MachineModel).filter(models.MachineModel.id == p.machine_model_id).first() if p.machine_model_id else None
        result.append({
            "id": p.id,
            "part_name": p.part_name,
            "part_number": p.part_number,
            "description": p.description,
            "photo_url": p.photo_url,
            "photo": p.photo,
            "price": p.price,
            "machine_id": p.machine_id,
            "machine_model_id": p.machine_model_id,
            "machine_name": machine.name if machine else None,
            "machine_model_name": model.model_name if model else None,
            "status": p.status,
            "created_at": p.created_at,
            "updated_at": p.updated_at
        })
    return result

@app.get("/parts/{part_id}", response_model=schemas.PartResponse)
def get_part(part_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Part).filter(models.Part.id == part_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Part not found")
    
    machine = db.query(models.Machine).filter(models.Machine.id == p.machine_id).first() if p.machine_id else None
    model = db.query(models.MachineModel).filter(models.MachineModel.id == p.machine_model_id).first() if p.machine_model_id else None
    
    return {
        "id": p.id,
        "part_name": p.part_name,
        "part_number": p.part_number,
        "description": p.description,
        "photo_url": p.photo_url,
        "photo": p.photo,
        "price": p.price,
        "machine_id": p.machine_id,
        "machine_model_id": p.machine_model_id,
        "machine_name": machine.name if machine else None,
        "machine_model_name": model.model_name if model else None,
        "status": p.status,
        "created_at": p.created_at,
        "updated_at": p.updated_at
    }

@app.post("/parts", response_model=schemas.PartResponse)
def create_part(part: schemas.PartCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Part).filter(models.Part.part_number == part.part_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Part number already exists")
    
    # Validate machine and model if provided
    if part.machine_id and not db.query(models.Machine).filter(models.Machine.id == part.machine_id).first():
        raise HTTPException(status_code=400, detail=f"Machine with ID {part.machine_id} not found")
    
    if part.machine_model_id and not db.query(models.MachineModel).filter(models.MachineModel.id == part.machine_model_id).first():
        raise HTTPException(status_code=400, detail=f"Machine Model with ID {part.machine_model_id} not found")

    new_part = models.Part(**part.dict())
    try:
        db.add(new_part)
        db.commit()
        db.refresh(new_part)
        
        machine = db.query(models.Machine).filter(models.Machine.id == new_part.machine_id).first() if new_part.machine_id else None
        model = db.query(models.MachineModel).filter(models.MachineModel.id == new_part.machine_model_id).first() if new_part.machine_model_id else None
        
        return {
            "id": new_part.id,
            "part_name": new_part.part_name,
            "part_number": new_part.part_number,
            "description": new_part.description,
            "photo_url": new_part.photo_url,
            "photo": new_part.photo,
            "price": new_part.price,
            "machine_id": new_part.machine_id,
            "machine_model_id": new_part.machine_model_id,
            "machine_name": machine.name if machine else None,
            "machine_model_name": model.model_name if model else None,
            "status": new_part.status,
            "created_at": new_part.created_at,
            "updated_at": new_part.updated_at
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/parts/{part_id}", response_model=schemas.PartResponse)
def update_part(part_id: int, part: schemas.PartUpdate, db: Session = Depends(get_db)):
    db_part = db.query(models.Part).filter(models.Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    if part.part_number:
        existing = db.query(models.Part).filter(models.Part.part_number == part.part_number, models.Part.id != part_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Part number already exists")

    # Validate machine and model if provided
    if part.machine_id and not db.query(models.Machine).filter(models.Machine.id == part.machine_id).first():
        raise HTTPException(status_code=400, detail=f"Machine with ID {part.machine_id} not found")
    
    if part.machine_model_id and not db.query(models.MachineModel).filter(models.MachineModel.id == part.machine_model_id).first():
        raise HTTPException(status_code=400, detail=f"Machine Model with ID {part.machine_model_id} not found")

    for key, value in part.dict(exclude_unset=True).items():
        setattr(db_part, key, value)
    
    try:
        db.commit()
        db.refresh(db_part)
        
        machine = db.query(models.Machine).filter(models.Machine.id == db_part.machine_id).first() if db_part.machine_id else None
        model = db.query(models.MachineModel).filter(models.MachineModel.id == db_part.machine_model_id).first() if db_part.machine_model_id else None
        
        return {
            "id": db_part.id,
            "part_name": db_part.part_name,
            "part_number": db_part.part_number,
            "description": db_part.description,
            "photo_url": db_part.photo_url,
            "photo": db_part.photo,
            "price": db_part.price,
            "machine_id": db_part.machine_id,
            "machine_model_id": db_part.machine_model_id,
            "machine_name": machine.name if machine else None,
            "machine_model_name": model.model_name if model else None,
            "status": db_part.status,
            "created_at": db_part.created_at,
            "updated_at": db_part.updated_at
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/parts/{part_id}")
def delete_part(part_id: int, db: Session = Depends(get_db)):
    db_part = db.query(models.Part).filter(models.Part.id == part_id).first()
    if not db_part:
        raise HTTPException(status_code=404, detail="Part not found")
    
    try:
        db.delete(db_part)
        db.commit()
        return {"message": "Part deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LOCATION APIs ====================
@app.get("/states")
def get_states(db: Session = Depends(get_db)):
    return db.query(models.State).order_by(models.State.id).all()

@app.post("/states")
def create_state(state: schemas.StateCreate, db: Session = Depends(get_db)):
    existing = db.query(models.State).filter(models.State.name == state.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="State already exists")
    
    new_state = models.State(
        name=state.name,
        code=state.code,
        zone=state.zone,
        mttr=state.mttr if state.mttr is not None else 0.0,
        status=state.status or "Active"
    )
    db.add(new_state)
    db.commit()
    db.refresh(new_state)
    return new_state

@app.put("/states/{state_id}")
def update_state(state_id: int, state_data: schemas.StateCreate, db: Session = Depends(get_db)):
    state = db.query(models.State).filter(models.State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    state.name = state_data.name
    state.code = state_data.code
    state.zone = state_data.zone
    if state_data.mttr is not None:
        state.mttr = state_data.mttr
    if state_data.status is not None:
        state.status = state_data.status
        
    db.commit()
    db.refresh(state)
    return state

@app.delete("/states/{state_id}")
def delete_state(state_id: int, db: Session = Depends(get_db)):
    state = db.query(models.State).filter(models.State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
        
    try:
        db.query(models.District).filter(models.District.state_id == state_id).delete()
        db.delete(state)
        db.commit()
        return {"message": "State deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/districts/{state_id}")
def get_districts(state_id: int, db: Session = Depends(get_db)):
    return db.query(models.District).filter(models.District.state_id == state_id).all()

@app.post("/districts")
def create_district(district: schemas.DistrictCreate, db: Session = Depends(get_db)):
    new_district = models.District(name=district.name, state_id=district.state_id)
    db.add(new_district)
    db.commit()
    db.refresh(new_district)
    return new_district

def get_zone_for_state(state_name: str) -> str:
    state_zones = {
        "Maharashtra": "West",
        "Gujarat": "West",
        "Rajasthan": "North",
        "Uttar Pradesh": "North",
        "Telangana": "South",
        "Tamil Nadu": "South",
        "Karnataka": "South",
        "Madhya Pradesh": "Central",
        "West Bengal": "East"
    }
    return state_zones.get(state_name, "West")

@app.get("/talukas", response_model=List[schemas.TalukaFullResponse])
def get_all_talukas(db: Session = Depends(get_db)):
    talukas = db.query(models.Taluka).all()
    result = []
    for t in talukas:
        district = db.query(models.District).filter(models.District.id == t.district_id).first()
        state = db.query(models.State).filter(models.State.id == district.state_id).first() if district else None
        
        result.append({
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "pincode": t.pincode,
            "status": t.status,
            "district_id": t.district_id,
            "district_name": district.name if district else "Unknown",
            "state_name": state.name if state else "Unknown",
            "zone": get_zone_for_state(state.name) if state else "West",
            "created_at": t.created_at
        })
    return result

@app.get("/talukas/{district_id}")
def get_talukas_by_district(district_id: int, db: Session = Depends(get_db)):
    return db.query(models.Taluka).filter(models.Taluka.district_id == district_id).all()

@app.post("/talukas")
def create_taluka(taluka: schemas.TalukaCreate, db: Session = Depends(get_db)):
    if not db.query(models.District).filter(models.District.id == taluka.district_id).first():
        raise HTTPException(status_code=400, detail="District not found")
        
    try:
        new_taluka = models.Taluka(
            name=taluka.name, 
            district_id=taluka.district_id,
            code=taluka.code,
            pincode=taluka.pincode,
            status=taluka.status or "Active"
        )
        db.add(new_taluka)
        db.commit()
        db.refresh(new_taluka)
        return new_taluka
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/talukas/{taluka_id}")
def update_taluka(taluka_id: int, taluka_data: schemas.TalukaUpdate, db: Session = Depends(get_db)):
    taluka = db.query(models.Taluka).filter(models.Taluka.id == taluka_id).first()
    if not taluka:
        raise HTTPException(status_code=404, detail="Taluka not found")
    
    if taluka_data.name is not None:
        taluka.name = taluka_data.name
    if taluka_data.district_id is not None:
        if not db.query(models.District).filter(models.District.id == taluka_data.district_id).first():
            raise HTTPException(status_code=400, detail="District not found")
        taluka.district_id = taluka_data.district_id
    if taluka_data.code is not None:
        taluka.code = taluka_data.code
    if taluka_data.pincode is not None:
        taluka.pincode = taluka_data.pincode
    if taluka_data.status is not None:
        taluka.status = taluka_data.status
        
    db.commit()
    db.refresh(taluka)
    return {"message": "Taluka updated successfully", "taluka_id": taluka.id}

@app.delete("/talukas/{taluka_id}")
def delete_taluka(taluka_id: int, db: Session = Depends(get_db)):
    taluka = db.query(models.Taluka).filter(models.Taluka.id == taluka_id).first()
    if not taluka:
        raise HTTPException(status_code=404, detail="Taluka not found")
    
    try:
        db.delete(taluka)
        db.commit()
        return {"message": "Taluka deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/villages")
def get_all_villages(db: Session = Depends(get_db)):
    return db.query(models.Village).all()

@app.get("/villages/{taluka_id}")
def get_villages_by_taluka(taluka_id: int, db: Session = Depends(get_db)):
    return db.query(models.Village).filter(models.Village.taluka_id == taluka_id).all()

@app.post("/villages")
def create_village(village: schemas.VillageCreate, db: Session = Depends(get_db)):
    if not db.query(models.Taluka).filter(models.Taluka.id == village.taluka_id).first():
        raise HTTPException(status_code=400, detail="Taluka not found")
        
    new_village = models.Village(name=village.name, taluka_id=village.taluka_id)
    db.add(new_village)
    db.commit()
    db.refresh(new_village)
    return new_village

@app.put("/villages/{village_id}")
def update_village(village_id: int, village_data: schemas.VillageUpdate, db: Session = Depends(get_db)):
    village = db.query(models.Village).filter(models.Village.id == village_id).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
        
    if village_data.taluka_id is not None:
        if not db.query(models.Taluka).filter(models.Taluka.id == village_data.taluka_id).first():
            raise HTTPException(status_code=400, detail="Taluka not found")
        village.taluka_id = village_data.taluka_id
        
    if village_data.name is not None:
        village.name = village_data.name
        
    db.commit()
    db.refresh(village)
    return {"message": "Village updated successfully", "village_id": village.id}

# ==================== COMMON LOCATION API ====================
@app.get("/locations/hierarchy", response_model=List[schemas.StateHierarchy])
def get_location_hierarchy(db: Session = Depends(get_db)):
    states = db.query(models.State).all()
    result = []
    for s in states:
        districts = db.query(models.District).filter(models.District.state_id == s.id).all()
        d_list = []
        for d in districts:
            talukas = db.query(models.Taluka).filter(models.Taluka.district_id == d.id).all()
            d_list.append({
                "id": d.id,
                "name": d.name,
                "talukas": [{"id": t.id, "name": t.name} for t in talukas]
            })
        result.append({
            "id": s.id,
            "name": s.name,
            "zone": s.zone,
            "districts": d_list
        })
    return result

@app.get("/locations")
def get_unified_locations(
    type: Optional[str] = None, 
    parent_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """
    Unified API for locations.
    - type: 'state', 'district', or 'taluka'
    - parent_id: state_id if type='district', or district_id if type='taluka'
    """
    if type == "district":
        query = db.query(models.District)
        if parent_id:
            query = query.filter(models.District.state_id == parent_id)
        return query.all()
    
    elif type == "taluka":
        query = db.query(models.Taluka)
        if parent_id:
            query = query.filter(models.Taluka.district_id == parent_id)
        return query.all()
    
    elif type == "village":
        query = db.query(models.Village)
        if parent_id:
            query = query.filter(models.Village.taluka_id == parent_id)
        return query.all()
    
    else: # Default to state
        return db.query(models.State).all()

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

# ==================== ATTENDANCE ====================
@app.post("/attendance/punch-in")
def punch_in(attendance: schemas.AttendanceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Admin can punch in for anyone, others only for themselves
    target_user_id = attendance.user_id if current_user.role == "admin" else current_user.id
    
    today = datetime.now().date()
    existing = db.query(models.Attendance).filter(
        models.Attendance.user_id == target_user_id,
        models.Attendance.date >= datetime.combine(today, datetime.min.time())
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"User {target_user_id} already punched in today")
    
    new_attendance = models.Attendance(
        user_id=target_user_id,
        punch_in=attendance.punch_in,
        punch_in_location=attendance.punch_in_location
    )
    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)
    return {"message": "Punch in successful", "attendance_id": new_attendance.id, "user_id": target_user_id}

@app.put("/attendance/punch-out")
def punch_out(attendance: schemas.AttendanceUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Admin can punch out for anyone, others only for themselves
    target_user_id = attendance.user_id if (current_user.role == "admin" and attendance.user_id) else current_user.id
    
    today = datetime.now().date()
    record = db.query(models.Attendance).filter(
        models.Attendance.user_id == target_user_id,
        models.Attendance.date >= datetime.combine(today, datetime.min.time())
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail=f"No punch in record found for user {target_user_id}")
    
    if record.punch_out:
        raise HTTPException(status_code=400, detail="Already punched out")
    
    record.punch_out = attendance.punch_out
    record.punch_out_location = attendance.punch_out_location
    if record.punch_in:
        hours = (attendance.punch_out - record.punch_in).total_seconds() / 3600
        record.hours_worked = round(hours, 2)
    
    db.commit()
    return {"message": "Punch out successful", "hours_worked": record.hours_worked, "user_id": target_user_id}

@app.get("/attendance/daily", response_model=List[schemas.AttendanceResponse])
def get_daily_attendance(db: Session = Depends(get_db)):
    try:
        attendances = db.query(
            models.Attendance,
            models.User.full_name.label("user_name")
        ).join(
            models.User, models.Attendance.user_id == models.User.id
        ).all()
        
        result = []
        for att, name in attendances:
            # Count activities (complaints assigned to this user on this day)
            activities = db.query(models.Complaint).filter(
                models.Complaint.assigned_to == att.user_id,
                func.date(models.Complaint.complaint_date) == func.date(att.date)
            ).count()
            
            result.append(schemas.AttendanceResponse(
                id=att.id,
                user_id=att.user_id,
                user_name=name or "Unknown",
                date=att.date,
                punch_in=att.punch_in,
                punch_out=att.punch_out,
                punch_in_location=att.punch_in_location,
                punch_out_location=att.punch_out_location,
                hours_worked=att.hours_worked,
                activities=activities
            ))
        return result
    except Exception as e:
        logger.error(f"Error fetching daily attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/monthly", response_model=List[schemas.MonthlyAttendanceResponse])
def get_monthly_attendance(month: Optional[str] = None, year: Optional[int] = None, db: Session = Depends(get_db)):
    try:
        now = datetime.now()
        target_month = month or now.strftime("%B")
        target_year = year or now.year
        
        # Convert month name to number
        try:
            month_num = list(calendar.month_name).index(target_month)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month name")
            
        # Get all service engineers
        engineers = db.query(models.User).filter(models.User.role == "service_engineer").all()
        
        result = []
        for eng in engineers:
            attendances = db.query(models.Attendance).filter(
                models.Attendance.user_id == eng.id,
                extract('month', models.Attendance.date) == month_num,
                extract('year', models.Attendance.date) == target_year
            ).all()
            
            present_days = len(attendances)
            total_hours = sum(att.hours_worked for att in attendances)
            avg_hours = total_hours / present_days if present_days > 0 else 0
            
            # Total activities for the month
            activities = db.query(models.Complaint).filter(
                models.Complaint.assigned_to == eng.id,
                extract('month', models.Complaint.complaint_date) == month_num,
                extract('year', models.Complaint.complaint_date) == target_year
            ).count()
            
            # Calculate absent days
            _, num_days = calendar.monthrange(target_year, month_num)
            
            result.append(schemas.MonthlyAttendanceResponse(
                user_id=eng.id,
                name=eng.full_name or eng.username,
                total_days=num_days,
                present_days=present_days,
                absent_days=num_days - present_days,
                total_hours=total_hours,
                avg_hours_per_day=round(avg_hours, 2),
                activities=activities,
                month=target_month,
                year=target_year
            ))
            
        return result
    except Exception as e:
        logger.error(f"Error fetching monthly attendance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
@app.get("/reviews", response_model=List[schemas.ReviewResponse])
def get_reviews(db: Session = Depends(get_db)):
    try:
        reviews = db.query(models.Review).all()
        result = []
        for r in reviews:
            complaint = db.query(models.Complaint).filter(models.Complaint.id == r.complaint_id).first()
            
            customer_name = "Unknown"
            if complaint:
                customer = db.query(models.Customer).filter(models.Customer.id == complaint.customer_id).first()
                if customer:
                    customer_user = db.query(models.User).filter(models.User.id == customer.user_id).first()
                    if customer_user:
                        customer_name = customer_user.full_name or customer_user.username
            
            engineer_name = "Not Assigned"
            if complaint and complaint.assigned_to:
                engineer = db.query(models.User).filter(models.User.id == complaint.assigned_to).first()
                if engineer:
                    engineer_name = engineer.full_name or engineer.username

            result.append({
                "id": r.id,
                "complaint_id": complaint.complaint_id if complaint else "Unknown",
                "customer_name": customer_name,
                "service_engineer_name": engineer_name,
                "rating": r.rating,
                "review_text": r.review_text,
                "created_at": r.created_at
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reviews")
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Find the customer record for this user
    customer = db.query(models.Customer).filter(models.Customer.user_id == current_user.id).first()
    if not customer:
        raise HTTPException(status_code=403, detail="Only customers can submit reviews")
        
    new_review = models.Review(
        complaint_id=review.complaint_id,
        customer_id=customer.id,
        rating=review.rating,
        review_text=review.review_text
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return {"message": "Review submitted successfully"}

# ==================== COLLECTIONS ====================
@app.get("/collections", response_model=List[schemas.CollectionResponse])
def get_collections(db: Session = Depends(get_db)):
    try:
        collections = db.query(models.Collection).all()
        result = []
        for col in collections:
            complaint = db.query(models.Complaint).filter(models.Complaint.id == col.complaint_id).first()
            
            customer_name = "Unknown"
            customer_mobile = "Unknown"
            se_name = "Not Assigned"
            warranty = "No"
            ticket_id = "Unknown"
            
            if complaint:
                ticket_id = complaint.complaint_id
                # Get Customer
                customer = db.query(models.Customer).filter(models.Customer.id == complaint.customer_id).first()
                if customer:
                    customer_user = db.query(models.User).filter(models.User.id == customer.user_id).first()
                    if customer_user:
                        customer_name = customer_user.full_name or customer_user.username
                        customer_mobile = customer_user.mobile or "Unknown"
                
                # Get SE
                if complaint.assigned_to:
                    engineer = db.query(models.User).filter(models.User.id == complaint.assigned_to).first()
                    if engineer:
                        se_name = engineer.full_name or engineer.username
                
                # Warranty logic (simplified)
                if complaint.warranty_date and complaint.warranty_date > datetime.now():
                    warranty = "Yes"
                elif complaint.installation_date:
                    # Assume 1 year warranty if not specified
                    from datetime import timedelta
                    if complaint.installation_date + timedelta(days=365) > datetime.now():
                        warranty = "Yes"

            result.append({
                "id": col.id,
                "ticket_id": ticket_id,
                "customer_name": customer_name,
                "customer_mobile": customer_mobile,
                "se_name": se_name,
                "warranty": warranty,
                "labour_charge": col.labour_charge,
                "local_part_amt": col.local_part_amt,
                "part_amt": col.part_amt,
                "total_amt": col.total_amt,
                "date": col.created_at.strftime("%Y-%m-%d") if col.created_at else "",
                "root_cause": col.root_cause or "-"
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collections")
def create_collection(collection: schemas.CollectionCreate, db: Session = Depends(get_db)):
    try:
        new_col = models.Collection(
            complaint_id=collection.complaint_id,
            labour_charge=collection.labour_charge,
            local_part_amt=collection.local_part_amt,
            part_amt=collection.part_amt,
            total_amt=collection.total_amt,
            root_cause=collection.root_cause
        )
        db.add(new_col)
        db.commit()
        db.refresh(new_col)
        return {"message": "Collection record created successfully", "id": new_col.id}
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REPORTS ====================
@app.get("/reports/dealer", response_model=List[schemas.DealerReportResponse])
def get_dealer_report(db: Session = Depends(get_db)):
    try:
        dealers = db.query(models.Dealer).all()
        result = []
        for d in dealers:
            # Get all complaints for this dealer
            complaints = db.query(models.Complaint).filter(models.Complaint.dealer_id == d.id).all()
            complaint_ids = [c.complaint_id for c in complaints]
            
            uw_visit = 0
            gw_visit = 0
            ow_visit = 0
            total_visits = len(complaints)
            labour_charge = 0
            spare_parts = 0
            total_collection = 0
            engineers = set()
            
            for c in complaints:
                # Warranty status
                if c.warranty_date and c.warranty_date > datetime.now():
                    uw_visit += 1
                else:
                    ow_visit += 1
                
                # Engineers
                if c.assigned_to:
                    eng = db.query(models.User).filter(models.User.id == c.assigned_to).first()
                    if eng:
                        engineers.add(eng.full_name or eng.username)
                
                # Financials from collections
                col = db.query(models.Collection).filter(models.Collection.complaint_id == c.id).first()
                if col:
                    labour_charge += col.labour_charge
                    spare_parts += (col.local_part_amt + col.part_amt)
                    total_collection += col.total_amt
            
            # Taluka Region
            taluka = db.query(models.Taluka).filter(models.Taluka.id == d.taluka_id).first()
            taluka_name = taluka.name if taluka else "Unknown"

            result.append({
                "id": d.id,
                "dealer_name": d.name,
                "taluka_region": taluka_name,
                "asm_rm_name": "N/A",
                "service_engineers": list(engineers),
                "uw_visit": uw_visit,
                "gw_visit": gw_visit,
                "ow_visit": ow_visit,
                "total_visits": total_visits,
                "labour_charge": labour_charge,
                "spare_parts": spare_parts,
                "total_collection": total_collection,
                "complaint_ids": complaint_ids,
                "description": f"Report for {d.name}",
                "customer_name": "Various"
            })
        return result
    except Exception as e:
        logger.error(f"Error in get_dealer_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/pocket", response_model=List[schemas.PocketReportResponse])
def get_pocket_report(db: Session = Depends(get_db)):
    try:
        # Group complaints by Dealer and Taluka (Pocket)
        # For simplicity, we iterate dealers and then their complaints' talukas
        dealers = db.query(models.Dealer).all()
        result = []
        sr_no = 1
        
        for d in dealers:
            # Grouping by Taluka (Pocket)
            talukas = db.query(models.Taluka).all()
            for t in talukas:
                # Find complaints for this dealer in this taluka
                complaints = db.query(models.Complaint).join(models.Customer).filter(
                    models.Complaint.dealer_id == d.id,
                    models.Customer.taluka_id == t.id
                ).all()
                
                if not complaints:
                    continue
                
                open_complaints = len([c for c in complaints if c.status in ["Pending", "Assigned", "In Progress"]])
                mtd_closed = len([c for c in complaints if c.status in ["Resolved", "Closed"]])
                
                # Engineers in this pocket for this dealer
                pocket_engineers = set()
                for c in complaints:
                    if c.assigned_to:
                        eng = db.query(models.User).filter(models.User.id == c.assigned_to).first()
                        if eng:
                            pocket_engineers.add(eng.full_name or eng.username)
                
                result.append({
                    "id": sr_no,
                    "sr_no": sr_no,
                    "dealer_name": d.name,
                    "asm_name": "N/A",
                    "pocket": t.name,
                    "service_engg_name": ", ".join(list(pocket_engineers)) if pocket_engineers else "N/A",
                    "location": f"{t.name}, Maharashtra",
                    "open_complaints": open_complaints,
                    "mtd_closed": mtd_closed,
                    "complaint_assigned": 0, # Placeholder for "today's" stats
                    "complaint_closed_on": 0,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                sr_no += 1
                
        return result
    except Exception as e:
        logger.error(f"Error in get_pocket_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CHECKSHEETS ====================
@app.get("/checksheets", response_model=List[schemas.CheckSheetResponse])
def get_checksheets(db: Session = Depends(get_db)):
    try:
        return db.query(models.CheckSheet).all()
    except Exception as e:
        logger.error(f"Error fetching checksheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checksheets")
def create_checksheet(checksheet: schemas.CheckSheetCreate, db: Session = Depends(get_db)):
    try:
        new_cs = models.CheckSheet(
            title=checksheet.title,
            description=checksheet.description,
            status=checksheet.status
        )
        db.add(new_cs)
        db.flush() # To get the id
        
        for section in checksheet.sections:
            new_section = models.CheckSheetSection(
                name=section.name,
                checksheet_id=new_cs.id
            )
            db.add(new_section)
            db.flush()
            
            for item in section.items:
                new_item = models.CheckSheetItem(
                    description=item.description,
                    is_required=item.is_required,
                    section_id=new_section.id
                )
                db.add(new_item)
        
        db.commit()
        return {"message": "Checksheet created successfully", "id": new_cs.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating checksheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/checksheets/{cs_id}")
def delete_checksheet(cs_id: int, db: Session = Depends(get_db)):
    try:
        cs = db.query(models.CheckSheet).filter(models.CheckSheet.id == cs_id).first()
        if not cs:
            raise HTTPException(status_code=404, detail="Checksheet not found")
        db.delete(cs)
        db.commit()
        return {"message": "Checksheet deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting checksheet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SERVICE ENGINEERS ====================
@app.get("/service-engineers", response_model=List[schemas.ServiceEngineerResponse])
def get_service_engineers(db: Session = Depends(get_db)):
    try:
        engineers = db.query(models.User).filter(models.User.role == "service_engineer").all()
        return engineers
    except Exception as e:
        logger.error(f"Error in get_service_engineers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/service-engineers")
def create_service_engineer(engineer: schemas.ServiceEngineerCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing = db.query(models.User).filter(
        (models.User.username == engineer.username) |
        (models.User.email == engineer.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = models.User(
        username=engineer.username,
        email=engineer.email,
        mobile=engineer.mobile,
        full_name=engineer.full_name,
        hashed_password=get_password_hash(engineer.mobile),  # default password = mobile
        role="service_engineer",
        address=engineer.address,
        state=engineer.state,
        district=engineer.district,
        taluka=engineer.taluka,
        is_team_lead=engineer.is_team_lead,
        is_under_dealer=engineer.is_under_dealer,
        status=engineer.status
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "Service engineer created successfully", "id": new_user.id, "full_name": new_user.full_name}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating service engineer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/service-engineers/{engineer_id}")
def delete_service_engineer(engineer_id: int, db: Session = Depends(get_db)):
    engineer = db.query(models.User).filter(models.User.id == engineer_id, models.User.role == "service_engineer").first()
    if not engineer:
        raise HTTPException(status_code=404, detail="Service engineer not found")
    db.delete(engineer)
    db.commit()
    return {"message": "Service engineer deleted"}

# ==================== TEAMS ====================
@app.get("/teams", response_model=List[schemas.TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    try:
        teams = db.query(models.Team).all()
        result = []
        for t in teams:
            lead = db.query(models.User).filter(models.User.id == t.team_lead_id).first()
            members = db.query(models.User).join(models.TeamMember).filter(models.TeamMember.team_id == t.id).all()
            result.append({
                "id": t.id,
                "name": t.name,
                "team_lead_id": t.team_lead_id,
                "team_lead_name": lead.full_name if (lead and lead.full_name) else "Unknown",
                "created_at": t.created_at,
                "members": members
            })
        return result
    except Exception as e:
        logger.error(f"Error in get_teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams")
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    # Validate team lead exists
    lead = db.query(models.User).filter(models.User.id == team.team_lead_id).first()
    if not lead:
        raise HTTPException(status_code=400, detail=f"Team lead with ID {team.team_lead_id} not found")

    # Validate all members exist
    for user_id in team.member_ids:
        member = db.query(models.User).filter(models.User.id == user_id).first()
        if not member:
            raise HTTPException(status_code=400, detail=f"Team member with ID {user_id} not found")

    new_team = models.Team(
        name=team.name,
        team_lead_id=team.team_lead_id
    )
    
    try:
        db.add(new_team)
        db.commit()
        db.refresh(new_team)

        # Add members
        for user_id in team.member_ids:
            member = models.TeamMember(team_id=new_team.id, user_id=user_id)
            db.add(member)
        
        db.commit()
        return {"message": "Team created successfully", "id": new_team.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating team: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Delete members first
    db.query(models.TeamMember).filter(models.TeamMember.team_id == team_id).delete()
    db.delete(team)
    db.commit()
    return {"message": "Team deleted successfully"}

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
            "status": cm.status or "Active"
        })
    return result

@app.post("/customer-machines")
def create_customer_machine(cm: schemas.CustomerMachineCreate, db: Session = Depends(get_db)):
    # Validate foreign keys
    if not db.query(models.Customer).filter(models.Customer.id == cm.customer_id).first():
        raise HTTPException(status_code=400, detail=f"Customer with ID {cm.customer_id} not found")
    
    if not db.query(models.Machine).filter(models.Machine.id == cm.machine_id).first():
        raise HTTPException(status_code=400, detail=f"Machine with ID {cm.machine_id} not found")
        
    if not db.query(models.MachineModel).filter(models.MachineModel.id == cm.machine_model_id).first():
        raise HTTPException(status_code=400, detail=f"Machine Model with ID {cm.machine_model_id} not found")
        
    if cm.service_engineer_id and not db.query(models.User).filter(models.User.id == cm.service_engineer_id).first():
        raise HTTPException(status_code=400, detail=f"Service Engineer with ID {cm.service_engineer_id} not found")
        
    if cm.dealer_id and not db.query(models.Dealer).filter(models.Dealer.id == cm.dealer_id).first():
        raise HTTPException(status_code=400, detail=f"Dealer with ID {cm.dealer_id} not found")

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
        dealer_id=cm.dealer_id,
        status=cm.status or "Active"
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

@app.delete("/customer-machines/{cm_id}")
def delete_customer_machine(cm_id: int, db: Session = Depends(get_db)):
    cm = db.query(models.CustomerMachine).filter(models.CustomerMachine.id == cm_id).first()
    if not cm:
        raise HTTPException(status_code=404, detail="Customer machine not found")
    
    db.delete(cm)
    db.commit()
    return {"message": "Customer machine deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)