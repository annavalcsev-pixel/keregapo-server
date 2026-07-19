from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime

class Discovery(Base):
    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    karakter = Column(String(50))
    korosztaly = Column(String(20))
    targy = Column(String(100))
    mese_szovege = Column(Text)
    idopont = Column(DateTime, default=datetime.datetime.utcnow)
