import json
from datetime import datetime, timedelta
from typing import List

from openpyxl.utils import get_column_letter
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import select, desc, func, update, Session
from fastapi import APIRouter, Query, Depends, Response
from pydash import get
from app.database import *

from app.crawler import *
from app.log import logger
import pandas as pd
from io import BytesIO
from app.aichat.flight_chat import get_flight_query_sql, gen_output_by_data

router = APIRouter(prefix="/ctrip", tags=["ctrip"])

class FlightListQuery(BaseModel):
    depTime: str| None = None
    depPort: str | None = None
    arrPort: str | None = None
    cabinClass:str | None = None


@router.get("/city_options")
def get_city_options():
    return [
        {
            'value': v,
            'label': k
        } for k, v in city_name_code_dict.items()
    ]


@router.get("/add_task")
def add_task(from_city: str, to_city: str, start_day: str, end_day: str, session: Session = Depends(get_session)):
    if not from_city or not get_city_code_by_city_name(from_city):
        return {'code': 400, 'msg': '出发城市错误'}
    if not to_city or not get_city_code_by_city_name(to_city):
        return {'code': 400, 'msg': '到达城市错误'}
    if not start_day or not end_day:
        return {'code': 400, 'msg': '出发日期错误'}
    start_day = datetime.strptime(start_day, '%Y-%m-%d').date()
    end_day = datetime.strptime(end_day, '%Y-%m-%d').date()

    current_day = start_day
    while current_day <= end_day:
        new_task = CtripTask(
            from_city=from_city,
            from_city_code=get_city_code_by_city_name(from_city),
            to_city=to_city,
            to_city_code=get_city_code_by_city_name(to_city),
            day=current_day,
        )
        session.add(new_task)
        current_day += timedelta(days=1)
    session.commit()
    return {'code': 200, }


@router.get("/page")
def page(page_num: int = Query(default=1),
         page_size: int = Query(default=20),
         session: Session = Depends(get_session)):
    offset = (page_num - 1) * page_size
    q = select(CtripTask).order_by(desc(CtripTask.create_time))

    total = session.exec(select(func.count()).select_from(q.subquery())).one()
    total_pages = (total + page_size - 1) // page_size

    tasks = (session.exec(q.offset(offset).limit(page_size)).all())

    return {
        'code': 200,
        'data': {
            "page_num": page_num,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "data": tasks
        }
    }


@router.get("/flight_page")
def flight_page(task_id: int = None,
                from_city: str = None,
                to_city: str = None,
                day: str = None,
                flight_no: str = None,
                page_num: int = Query(default=1),
                page_size: int = Query(default=20),
                session: Session = Depends(get_session)):
    offset = (page_num - 1) * page_size
    q = select(CtripFlight).where(CtripFlight.is_latest == True)

    if task_id is not None:
        q = q.where(CtripFlight.task_id == task_id)
    if flight_no is not None:
        q = q.where(CtripFlight.flight_no == flight_no)
    if from_city is not None:
        q = q.where(CtripFlight.from_city == from_city)
    if to_city is not None:
        q = q.where(CtripFlight.to_city == to_city)
    if day is not None:
        q = q.where(CtripFlight.day == datetime.strptime(day, '%Y-%m-%d').date())

    total = session.exec(select(func.count()).select_from(q.subquery())).one()

    # 查询总记录数
    tasks = (session.exec(q.order_by(desc(CtripFlight.day)).offset(offset).limit(page_size)).all())

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size

    return {
        'code': 200,
        'data': {
            "page_num": page_num,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "data": tasks
        }
    }

@router.post("/flight_list")
def flight_page(query : FlightListQuery,
                session: Session = Depends(get_session)):
    q = select(CtripFlight).where(CtripFlight.is_latest == True)

    if query.cabinClass is not None:
        q = q.where(CtripFlight.cabin == query.cabinClass)
    if query.depPort is not None:
        q = q.where(CtripFlight.from_city == query.depPort)
    if query.arrPort is not None:
        q = q.where(CtripFlight.to_city == query.arrPort)
    if query.depTime is not None:
        q = q.where(CtripFlight.day == datetime.strptime(query.depTime, '%Y-%m-%d').date())

    tasks = (session.exec(q.order_by(desc(CtripFlight.day))).all())

    return {
        'code': 200,
        'data': tasks
    }


@router.get('/excel-export')
def excel_export(task_id: int = None,
                 from_city: str = None,
                 to_city: str = None,
                 day: str = None,
                 flight_no: str = None,
                 session: Session = Depends(get_session)):
    q = select(CtripFlight).where(CtripFlight.is_latest == True)

    if task_id is not None:
        q = q.where(CtripFlight.task_id == task_id)
    if flight_no is not None:
        q = q.where(CtripFlight.flight_no == flight_no)
    if from_city is not None:
        q = q.where(CtripFlight.from_city == from_city)
    if to_city is not None:
        q = q.where(CtripFlight.to_city == to_city)
    if day is not None:
        q = q.where(CtripFlight.day == datetime.strptime(day, '%Y-%m-%d').date())

    flights: List[CtripFlight] = session.exec(q.order_by(desc(CtripFlight.day))).all()

    df = pd.DataFrame([{
        'TaskId': it.task_id,
        '航班号': it.flight_no,
        '航线': f'{it.from_city}({it.departure_airport_name}) - {it.to_city}({it.arrival_airport_name})',
        '航班日期': it.day.strftime('%Y-%m-%d'),
        'MarketAirline': it.airline_name,
        'OperateAirline': it.operate_airline_name,
        '机型': it.aircraft_name,
        '票价': it.adult_price,
        '折扣': it.discount_rate,
        'Cabin': it.cabin,
        'Invoice Type': it.invoice_type
    } for it in flights])
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        worksheet = writer.sheets['Sheet1']
        for col in df.columns:
            col_idx = df.columns.get_loc(col) + 1
            col_letter = get_column_letter(col_idx)
            if col_letter == 'C':
                worksheet.column_dimensions[col_letter].width = 50
            else:
                worksheet.column_dimensions[col_letter].width = 20

    excel_data = output.getvalue()

    return Response(content=excel_data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename=output.xlsx"})


@router.get("/take")
def take_task(session: Session = Depends(get_session)):
    task: CtripTask = session.exec(
        select(CtripTask).where(CtripTask.status == 'PENDING').order_by(CtripTask.create_time).limit(1)).first()
    if task is None:
        return {'code': 200}
    task.status = 'PROCESSING'
    task.process_start_time = datetime.now()
    session.commit()
    return {'code': 200, 'task': {
        'from_city': task.from_city,
        'from_city_code': task.from_city_code,
        'to_city': task.to_city,
        'to_city_code': task.to_city_code,
        'day': task.day.strftime('%Y-%m-%d'),
        'id': task.id,
    }}


class TaskComplete(BaseModel):
    task_id: int
    data: dict


@router.post("/complete")
def complete_task(task_complete: TaskComplete, session: Session = Depends(get_session)):
    if_success = len(get(task_complete.data, 'data.flightItineraryList', [])) > 0
    task = session.exec(select(CtripTask).where(CtripTask.id == task_complete.task_id)).one()
    task.status = 'SUCCESS' if if_success else 'FAIL'
    task.process_end_time = datetime.now()

    if if_success:
        ctrip_origin_json = CtripOriginJson(task_id=task.id, origin_json=task_complete.data)
        session.add(ctrip_origin_json)
    session.commit()
    session.refresh(task)

    if if_success:
        flights = extract_flight_info_from_origin_data(task_complete.data.get('data'))
        if flights:
            now = datetime.now()
            session.exec(update(CtripFlight).where((CtripFlight.from_city_code == task.from_city_code) & (
                    CtripFlight.to_city_code == task.to_city_code) & (CtripFlight.day == task.day) & (
                                                           CtripFlight.is_latest == True)).values(
                is_latest=False))
            for flight in flights:
                ctrip_flight = CtripFlight(
                    task_id=task.id,
                    data_time=now,
                    from_city=task.from_city,
                    from_city_code=task.from_city_code,
                    to_city=task.to_city,
                    to_city_code=task.to_city_code,
                    day=task.day,
                    airline_name=flight.airline_name,
                    flight_no=flight.flight_no,
                    aircraft_code=flight.aircraft_code,
                    aircraft_name=flight.aircraft_name,
                    operate_airline_name=flight.operate_airline_name,
                    departure_city_code=flight.departure_city_code,
                    departure_city_name=flight.departure_city_name,
                    departure_airport_name=flight.departure_airport_name,
                    arrival_city_name=flight.arrival_city_name,
                    arrival_city_code=flight.arrival_city_code,
                    arrival_airport_name=flight.arrival_airport_name,
                    adult_price=flight.adult_price,
                    invoice_type=flight.invoice_type,
                    cabin=flight.cabin,
                    is_latest=True,
                    discount_rate=flight.discount_rate,
                )
                session.add(ctrip_flight)
                session.flush()
                session.add(CtripFlightJson(
                    flight_id=ctrip_flight.id,
                    data_json=flight.origin_json
                ))
            session.commit()
    return {'code': 200}


@router.get("/chat")
def get_demo_data(user_input: str, session: Session = Depends(get_session)):
    flight_query_sql = get_flight_query_sql(user_input)
    if flight_query_sql is None:
        return {'code': 500, 'error': '查询失败'}
    db_result = session.execute(text(flight_query_sql))
    result_list = db_result.mappings().all()
    return {'code':200, 'data':gen_output_by_data(user_input, result_list)}

