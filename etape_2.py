# coding: utf-8
import datetime
import json
import typing

import aiohttp_autoreload
import serpyco
from aiohttp import web
from hapic import Hapic, HapicData
from hapic.error.serpyco import SerpycoDefaultErrorBuilder
from hapic.ext.aiohttp.context import AiohttpContext
from hapic.processor.serpyco import SerpycoProcessor

from dataclasses import dataclass

import utils

hapic = Hapic(async_=True)
hapic.set_processor_class(SerpycoProcessor)


@dataclass
class Location(object):
    def get_openstreetmap_url(obj: "Location") -> str:
        return f"https://www.openstreetmap.org/search?#map=13/{obj.lat}/{obj.lon}"

    lon: float = serpyco.number_field(cast_on_load=True)
    lat: float = serpyco.number_field(cast_on_load=True)
    url: typing.Optional[str] = serpyco.string_field(
        getter=get_openstreetmap_url, default=None
    )


@dataclass
class Sensor:
    name: str
    location: Location = None


@dataclass
class About(object):
    current_datetime: datetime.datetime
    ip: str

    @staticmethod
    @serpyco.post_dump
    def add_python_version(data: dict) -> dict:
        data["python_version"] = utils.get_python_version()
        return data


sensor = Sensor(name="<no name>", location=Location(lon=19, lat=32))


@dataclass
class EmptyPath(object):
    pass


@dataclass
class SensorName:
    name: str


@hapic.with_api_doc()
@hapic.output_body(About)
async def GET_about(request):
    return About(current_datetime=datetime.datetime.now(), ip=utils.get_ip())


@hapic.with_api_doc()
@hapic.input_path(EmptyPath)
@hapic.input_body(SensorName)
@hapic.output_body(Sensor)
async def PUT_sensor_name(request, hapic_data: HapicData):
    print(hapic_data.body)
    sensor.name = hapic_data.body.name
    return sensor


@hapic.with_api_doc()
@hapic.input_path(EmptyPath)
@hapic.input_body(Location)
@hapic.output_body(Sensor)
async def PUT_sensor_location(request, hapic_data: HapicData):
    print(hapic_data.body)
    sensor.location = Location(lat=hapic_data.body.lat, lon=hapic_data.body.lon)
    return sensor


@hapic.with_api_doc()
@hapic.output_body(Sensor)
async def GET_sensor(request):
    return sensor


app = web.Application()
app.add_routes(
    [
        web.get(r"/about", GET_about),
        web.put(r"/sensor/name", PUT_sensor_name),
        web.put(r"/sensor/location", PUT_sensor_location),
        web.get(r"/sensor", GET_sensor),
    ]
)

hapic.set_context(
    AiohttpContext(app, default_error_builder=SerpycoDefaultErrorBuilder())
)

hapic.add_documentation_view("/api/doc", "DOC", "Generated doc")
print(json.dumps(hapic.generate_doc()))
aiohttp_autoreload.start()
web.run_app(app)
