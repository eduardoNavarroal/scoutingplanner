import os
import shutil
from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import FastAPI


from fastapi import (
    FastAPI, Depends, HTTPException, status,
    UploadFile, File, Form, Body
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from . import models, schemas, database
from .models import User, Profile, ScoutGroup, Team, Membership, Appearance
from .schemas import (
    UserRead, UserCreate, UserUpdate, Token,
    ProfileRead, ProfileCreate, ProfileUpdate,
    ScoutGroupRead, ScoutGroupCreate, ScoutGroupUpdate,
    TeamRead, TeamCreate, TeamUpdate,
    MembershipRead, MembershipCreate,
    AppearanceRead, AppearanceUpdate
)

# Configuración de seguridad
SECRET_KEY = "cambia_esto_por_una_clave_muy_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# App y CORS
app = FastAPI()   # <-- PRIMERO SE CREA LA APP

# LUEGO se agrega el middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.18.2:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static
app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("static/photos", exist_ok=True)
database.init_db()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_error
    except JWTError:
        raise credentials_error
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_error
    return user

# -----------------------
# AUTENTICACIÓN
# -----------------------

@app.post("/auth/register", response_model=UserRead, tags=["auth"])
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    hashed_password = user_in.password  # Ajusta a tu hash real si usas bcrypt
    user = User(email=user_in.email, hashed_password=hashed_password, role=user_in.role or "caminante")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or user.hashed_password != form_data.password:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# -----------------------
# USUARIO
# -----------------------

@app.get("/users/me", response_model=UserRead, tags=["users"])
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users", response_model=List[UserRead], tags=["users"])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden listar usuarios.")
    return db.query(User).all()

@app.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver usuarios.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@app.post("/users", response_model=UserRead, tags=["users"])
def create_user(user_in: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear usuarios.")
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado.")
    hashed_password = user_in.password
    user = User(email=user_in.email, hashed_password=hashed_password, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.put("/users/{user_id}", response_model=UserRead, tags=["users"])
def update_user(
    user_id: int,
    user_in: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar usuarios.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    user.email = user_in.email or user.email
    if user_in.password:
        user.hashed_password = user_in.password
    user.role = user_in.role or user.role
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar usuarios.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    db.delete(user)
    db.commit()
    return {"ok": True}

# -----------------------
# PERFIL
# -----------------------

@app.get("/users/me/profile", response_model=ProfileRead, tags=["profile"])
def read_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return profile

@app.put("/users/me/profile", response_model=ProfileRead, tags=["profile"])
async def upsert_my_profile(
    nombre: str = Form(...),
    apellido: str = Form(...),
    fecha_nac: date = Form(...),
    departamento: str = Form(...),
    distrito: str = Form(...),
    telefono: Optional[str] = Form(None),
    grupo_scout: Optional[str] = Form(None),
    comunidad: Optional[str] = Form(None),
    direccion: Optional[str] = Form(None),
    redes_sociales: Optional[str] = Form(None),
    foto: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if profile:
        for field, value in {
            "nombre": nombre, "apellido": apellido, "telefono": telefono, "fecha_nac": fecha_nac,
            "grupo_scout": grupo_scout, "comunidad": comunidad, "direccion": direccion,
            "redes_sociales": redes_sociales, "departamento": departamento, "distrito": distrito
        }.items():
            if value is not None:
                setattr(profile, field, value)
    else:
        profile = Profile(
            user_id=current_user.id, nombre=nombre, apellido=apellido, telefono=telefono,
            fecha_nac=fecha_nac, grupo_scout=grupo_scout, comunidad=comunidad, direccion=direccion,
            redes_sociales=redes_sociales, departamento=departamento, distrito=distrito
        )
        db.add(profile)
    if foto:
        filename = f"{current_user.id}_{foto.filename}"
        file_path = os.path.join("static/photos", filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        # Devuelve una URL absoluta para la foto:
        profile.foto_url = f"{os.getenv('BACKEND_URL') or 'http://localhost:8000'}/static/photos/{filename}"
    db.commit()
    db.refresh(profile)
    return profile

# -----------------------
# APPEARANCE (CAMBIO DE PORTADA)
# -----------------------

@app.get("/appearance", response_model=AppearanceRead, tags=["appearance"])
def get_appearance(db: Session = Depends(get_db)):
    appearance = db.query(Appearance).first()
    if not appearance:
        # Valor por defecto si no existe registro
        return AppearanceRead(portada_url="")
    return appearance

@app.put("/appearance", response_model=AppearanceRead, tags=["appearance"])
async def update_appearance(
    portada: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar la portada.")
    filename = f"Portada-600-x-400px.jpg"
    file_path = os.path.join("static/photos", filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(portada.file, buffer)
    portada_url = f"{os.getenv('BACKEND_URL') or 'http://localhost:8000'}/static/photos/{filename}"
    appearance = db.query(Appearance).first()
    if appearance:
        appearance.portada_url = portada_url
    else:
        appearance = Appearance(portada_url=portada_url)
        db.add(appearance)
    db.commit()
    db.refresh(appearance)
    return appearance

# -----------------------
# SCOUT GROUP
# -----------------------

@app.get("/scout-groups", response_model=List[ScoutGroupRead], tags=["scout-groups"])
def list_scout_groups(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Sin permiso para ver grupos scout")
    return db.query(ScoutGroup).all()

@app.post("/scout-groups", response_model=ScoutGroupRead, tags=["scout-groups"])
def create_scout_group(
    data: ScoutGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear grupos scout")
    grupo = ScoutGroup(**data.dict())
    db.add(grupo)
    db.commit()
    db.refresh(grupo)
    return grupo

@app.put("/scout-groups/{group_id}", response_model=ScoutGroupRead, tags=["scout-groups"])
def update_scout_group(
    group_id: int,
    data: ScoutGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar grupos scout")
    grupo = db.query(ScoutGroup).filter(ScoutGroup.id == group_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo scout no encontrado")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(grupo, key, value)
    db.commit()
    db.refresh(grupo)
    return grupo

@app.delete("/scout-groups/{group_id}", tags=["scout-groups"])
def delete_scout_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar grupos scout")
    grupo = db.query(ScoutGroup).filter(ScoutGroup.id == group_id).first()
    if not grupo:
        raise HTTPException(status_code=404, detail="Grupo scout no encontrado")
    db.delete(grupo)
    db.commit()
    return {"ok": True}

# -----------------------
# TEAMS y MEMBERSHIPS
# -----------------------

@app.get("/teams", response_model=List[TeamRead], tags=["teams"])
def list_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "administrador":
        return db.query(Team).all()
    elif current_user.role == "coordinador":
        return db.query(Team).filter(Team.coordinador_id == current_user.id).all()
    else:
        raise HTTPException(status_code=403, detail="Sin permiso para listar equipos")

@app.post("/teams", response_model=TeamRead, tags=["teams"])
def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "coordinador":
        raise HTTPException(status_code=403, detail="Solo coordinadores pueden crear equipos")
    equipo = Team(**data.dict())
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    return equipo

@app.put("/teams/{team_id}", response_model=TeamRead, tags=["teams"])
def update_team(
    team_id: int,
    data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or (current_user.role == "coordinador" and team.coordinador_id != current_user.id):
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este equipo")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(team, key, value)
    db.commit()
    db.refresh(team)
    return team

@app.delete("/teams/{team_id}", tags=["teams"])
def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or (current_user.role == "coordinador" and team.coordinador_id != current_user.id):
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este equipo")
    db.delete(team)
    db.commit()
    return {"ok": True}

@app.get("/memberships", response_model=List[MembershipRead], tags=["memberships"])
def list_memberships(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "administrador":
        return db.query(Membership).all()
    else:
        equipos = db.query(Team).filter(Team.coordinador_id == current_user.id).all()
        equipo_ids = [e.id for e in equipos]
        return db.query(Membership).filter(Membership.team_id.in_(equipo_ids)).all()

@app.post("/memberships", response_model=MembershipRead, tags=["memberships"])
def create_membership(
    data: MembershipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    equipo = db.query(Team).filter(Team.id == data.team_id).first()
    if not equipo or equipo.coordinador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el coordinador del equipo puede asignar miembros")
    membership = Membership(**data.dict())
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership

@app.delete("/memberships/{membership_id}", tags=["memberships"])
def delete_membership(
    membership_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = db.query(Membership).filter(Membership.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membresía no encontrada")
    equipo = db.query(Team).filter(Team.id == membership.team_id).first()
    if not equipo or (current_user.role != "administrador" and equipo.coordinador_id != current_user.id):
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar esta membresía")
    db.delete(membership)
    db.commit()
    return {"ok": True}

# -----------------------
# ENDPOINT DE TEST
# -----------------------
@app.get("/", tags=["test"])
def root():
    return {"message": "API de Scouting Planner lista 🚀"}

