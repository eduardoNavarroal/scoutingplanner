# app/models.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

# ---------------------------
# USUARIO Y PERFIL
# ---------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="caminante", nullable=False)

    # Relación con el perfil
    profile = relationship("Profile", uselist=False, back_populates="user", cascade="all, delete")
    # Opcional: puedes agregar relationships con Teams/ScoutGroups si lo ves necesario

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String, nullable=True)
    fecha_nac = Column(Date, nullable=True)
    foto_url = Column(String, nullable=True)
    grupo_scout = Column(String, nullable=True)
    comunidad = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    redes_sociales = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
    distrito = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

# ---------------------------
# GRUPO SCOUT
# ---------------------------
class ScoutGroup(Base):
    __tablename__ = "scoutgroups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    region = Column(String, nullable=True)
    localidad = Column(String, nullable=True)
    district = Column(String, nullable=True)
    numeral = Column(String, nullable=True)
    address = Column(String, nullable=True)
    office_hours = Column(String, nullable=True)
    group_leader_name = Column(String, nullable=True)
    group_leader_email = Column(String, nullable=True)
    group_leader_phone = Column(String, nullable=True)

# ---------------------------
# APARIENCIA / CONFIGURACIÓN GENERAL (Ejemplo: portada editable)
# ---------------------------
class Appearance(Base):
    __tablename__ = "appearance"

    id = Column(Integer, primary_key=True, index=True)
    portada_url = Column(String, nullable=True)
    # Puedes agregar más campos configurables si lo necesitas (colores, textos, etc.)

# ---------------------------
# EQUIPOS Y MEMBRESÍAS
# ---------------------------
class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    coordinador_id = Column(Integer, ForeignKey("users.id"))
    scout_group_id = Column(Integer, ForeignKey("scoutgroups.id"))
    avatar_url = Column(String, nullable=True)
    history = Column(Text, nullable=True)
    creation_date = Column(Date, nullable=True)
    community_name = Column(String, nullable=True)
    unlocked_achievements_count = Column(Integer, default=0, nullable=False)

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    perfil_id = Column(Integer, ForeignKey("profiles.id"))

# ---------------------------
# Puedes seguir agregando aquí los modelos para Logros, Challenges, Ciclos, etc.
# Si necesitas que los incluya, dímelo antes de seguir con los endpoints.
