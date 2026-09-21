from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RespondentRecord(Base):
    __tablename__ = "respondent_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time_stamp = Column(String, nullable=True)
    age = Column(Integer, nullable=False)
    gender= Column(String, nullable=False)
    country= Column(String, nullable=False)
    state_= Column(String, nullable=True)
    self_employed = Column(String, nullable=True)
    family_history = Column(String, nullable=True)
    treatment = Column(String, nullable=False)
    work_interference_level = Column(String, nullable=True)
    no_employees= Column(String, nullable=False)
    remote_work = Column(String, nullable=False)
    tech_company = Column(String, nullable=True)
    benefits = Column(String, nullable=False)
    care_options = Column(String, nullable = False)
    wellness_program = Column(String, nullable= True)
    seek_help = Column(String, nullable= True)
    anonymity = Column(String, nullable=True)
    leave = Column(String, nullable= True )
    mental_health_consequence= Column(String, nullable=True)
    phys_health_consequence = Column(String, nullable=True)
    coworkers = Column(String, nullable= True )
    supervisor = Column(String, nullable= True)
    mental_health_interview = Column(String, nullable= True)
    phys_health_interview = Column(String, nullable=True)
    mental_vs_physical = Column(String, nullable=True)
    obs_consequence = Column(String, nullable=True)
    comments = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("age >= 18 AND age <= 100", name ="chk_valid_age"),
    ) 

    