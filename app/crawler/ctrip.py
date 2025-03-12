import pathlib
from collections import namedtuple
from pydash import get
import json
from app.config import resource_path

with open(resource_path / 'city.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

city_name_code_dict = {value: key for key, value in data.items()}

def get_city_code_by_city_name(city_name: str) -> str | None:
    return city_name_code_dict.get(city_name)


Flight = namedtuple('Flight',
                    ['airline_name', 'flight_no', 'aircraft_code', 'aircraft_name', 'operate_airline_name',
                     'departure_city_code', 'departure_city_name',
                     'departure_airport_name', 'departure_date_time',
                     'arrival_city_name', 'arrival_city_code', 'arrival_airport_name', 'arrival_date_time', 'adult_price', 'invoice_type',
                     'cabin',
                     'discount_rate', 'origin_json'])


def extract_flight_info_from_origin_data(flight_data: dict) -> list[Flight]:
    if flight_data is None:
        return []

    flights = get(flight_data, 'flightItineraryList', None)
    if flight_data is None or flights is None or len(flights) == 0:
        return []

    flight_data = [it for it in flights if len(get(it, 'flightSegments[0].flightList', [])) == 1]

    if not flight_data:
        return []

    flights_result = []
    for it in flight_data:
        flight_part = get(it, 'flightSegments[0].flightList[0]', None)
        price_part = get(it, 'priceList[0]', None)

        target_flight = Flight(airline_name=get(flight_part, 'marketAirlineName', None),
                               flight_no=get(flight_part, 'flightNo', None),
                               aircraft_code=get(flight_part, 'aircraftCode', None),
                               aircraft_name=get(flight_part, 'aircraftName', None),
                               operate_airline_name=get(flight_part, 'operateAirlineName', None),
                               departure_city_code=get(flight_part, 'departureCityCode', None),
                               departure_city_name=get(flight_part, 'departureCityName', None),
                               departure_airport_name=get(flight_part, 'departureAirportName', None),
                               departure_date_time=get(flight_part, 'departureDateTime', None),
                               arrival_city_code=get(flight_part, 'arrivalCityCode', None),
                               arrival_city_name=get(flight_part, 'arrivalCityName', None),
                               arrival_airport_name=get(flight_part, 'arrivalAirportName', None),
                               arrival_date_time=get(flight_part, 'arrivalDateTime', None),
                               adult_price=get(price_part, 'adultPrice', None),
                               invoice_type=get(price_part, 'invoiceType', None),
                               cabin=get(price_part, 'cabin', None),
                               discount_rate=get(price_part, 'priceUnitList[0].flightSeatList[0].discountRate', None),
                               origin_json={
                                   'flight': flight_part,
                                   'price': price_part
                               })
        flights_result.append(target_flight)
    return flights_result
