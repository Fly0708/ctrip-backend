from sqlalchemy import Column
from sqlmodel import SQLModel, Field, JSON
from datetime import date, datetime


class CtripTask(SQLModel, table=True):
    __tablename__ = 'ctrip_task'

    id: int | None = Field(primary_key=True)
    from_city: str
    from_city_code: str
    to_city: str
    to_city_code: str
    day: date
    status: str = Field(default='PENDING', description='PENDING, PROCESSING, SUCCESS, FAIL')

    process_start_time: datetime | None
    process_end_time: datetime | None
    create_time: datetime | None
    update_time: datetime | None


class CtripOriginJson(SQLModel, table=True):
    __tablename__ = 'ctrip_origin_json'
    id: int | None = Field(primary_key=True)
    task_id: int | None
    origin_json: JSON | None = Field(sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True


class CtripFlight(SQLModel, table=True):
    __tablename__ = 'ctrip_flight'

    id: int | None = Field(primary_key=True)
    task_id: int
    data_time: datetime = Field(default_factory=datetime.now)
    from_city: str
    from_city_code: str
    to_city: str
    to_city_code: str
    day: date
    airline_name: str | None
    flight_no: str | None
    aircraft_code: str | None
    aircraft_name: str | None
    operate_airline_name: str | None
    departure_city_code: str | None
    departure_city_name: str | None
    departure_airport_name: str | None
    arrival_city_name: str | None
    arrival_city_code: str | None
    arrival_airport_name: str | None
    adult_price: str | None
    invoice_type: str | None
    cabin: str | None
    discount_rate: str | None
    is_latest: bool = Field(default=True)
    create_time: datetime | None
    update_time: datetime | None


class CtripFlightJson(SQLModel, table=True):
    __tablename__ = 'ctrip_flight_json'
    id: int | None = Field(primary_key=True)
    flight_id: int
    data_json: JSON | None  = Field(sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True
