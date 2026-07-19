from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
import datetime

class Discovery(Base):
    __tablename__ = "discoveries"

    id = Column(Integer, primary_key=True, index=True)
    karakter = Column(String(50))      # Ki mesélt?
    korosztaly = Column(String(20))    # Kinek?
    targy = Column(String(100))        # Mit talált?
    mese_szovege = Column(Text)        # Mit mondott a Gemini?
    idopont = Column(DateTime, default=datetime.datetime.utcnow)