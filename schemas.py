from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

# ----------- USUARIOS -----------
class UserBase(BaseModel):
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserRead(UserBase):
    id: int
    class Config:
        from_attributes = True

# ----------- PERFIL -----------
class ProfileBase(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nac: Optional[date] = None
    grupo_scout: Optional[str] = None
    comunidad: Optional[str] = None
    direccion: Optional[str] = None
    redes_sociales: Optional[str] = None
    departamento: Optional[str] = None
    distrito: Optional[str] = None
    foto_url: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileRead(ProfileBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

# ----------- GRUPO SCOUT -----------
class ScoutGroupBase(BaseModel):
    nombre: Optional[str] = None
    distrito: Optional[str] = None
    descripcion: Optional[str] = None
    foto_url: Optional[str] = None

class ScoutGroupCreate(ScoutGroupBase):
    nombre: str

class ScoutGroupUpdate(ScoutGroupBase):
    pass

class ScoutGroupRead(ScoutGroupBase):
    id: int
    class Config:
        from_attributes = True

# ----------- EQUIPO (TEAM) -----------
class TeamBase(BaseModel):
    nombre: Optional[str] = None
    grupo_scout_id: Optional[int] = None
    coordinador_id: Optional[int] = None
    descripcion: Optional[str] = None

class TeamCreate(TeamBase):
    nombre: str
    grupo_scout_id: int

class TeamUpdate(TeamBase):
    pass

class TeamRead(TeamBase):
    id: int
    class Config:
        from_attributes = True

# ----------- MEMBRESÍAS -----------
class MembershipBase(BaseModel):
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    rol: Optional[str] = None

class MembershipCreate(MembershipBase):
    user_id: int
    team_id: int
    rol: str

class MembershipUpdate(MembershipBase):
    pass

class MembershipRead(MembershipBase):
    id: int
    class Config:
        from_attributes = True

# ----------- APPEARANCE (Personalización) -----------
class AppearanceBase(BaseModel):
    portada_url: Optional[str] = None

class AppearanceCreate(AppearanceBase):
    pass

class AppearanceUpdate(AppearanceBase):
    pass

class AppearanceRead(AppearanceBase):
    id: int
    class Config:
        from_attributes = True

# ----------- TOKEN (LOGIN) -----------
class Token(BaseModel):
    access_token: str
    token_type: str

# ----------- OTROS MODELOS (ejemplo para logros, retos, etc.) -----------
class LogroBase(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class LogroCreate(LogroBase):
    nombre: str

class LogroUpdate(LogroBase):
    pass

class LogroRead(LogroBase):
    id: int
    class Config:
        from_attributes = True

# Si tienes Challenge, ProgramCycle, etc., sigue el mismo patrón

