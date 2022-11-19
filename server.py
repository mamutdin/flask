from typing import Type, Union, Optional

import pydantic as pydantic
from flask import Flask, jsonify, request
from flask.views import MethodView
from sqlalchemy import Column, Integer, String, DateTime, create_engine, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

app = Flask('app')
DSN = 'postgresql://postgres:postgres@127.0.0.1:5432/flask'


class HTTPError(Exception):
    def __init__(self, status_code: int, message: Union[str, list, dict]):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HTTPError)
def error_handler(error: HTTPError):
    response = jsonify({
        'status': 'error', 'message': error.message
    })
    response.status_code = error.status_code
    return response


engine = create_engine(DSN)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class AdvModel(Base):
    __tablename__ = 'advs'

    id = Column(Integer, primary_key=True)
    title = Column(String(32), nullable=False, unique=True)
    description = Column(String(200))
    create_time = Column(DateTime, server_default=func.now())
    owner = Column(String(50))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    email = Column(String(200))


Base.metadata.create_all(engine)


class CreateAdvModel(pydantic.BaseModel):
    title: str

    @pydantic.validator('title')
    def check_name(cls, value: str):
        if len(value) > 32:
            raise ValueError('name is too long')
        return value


class PatchAdvModel(pydantic.BaseModel):
    title: str
    description: Optional[str]
    owner: Optional[str]

    @pydantic.validator('title')
    def check_name(cls, value: str):
        if len(value) > 32:
            raise ValueError('name is too long')
        return value


def validate(data_to_validate: dict, validation_class: Type[CreateAdvModel] | Type[PatchAdvModel]):
    try:
        return validation_class(**data_to_validate).dict(exclude_none=True)
    except pydantic.ValidationError as err:
        raise HTTPError(400, err.errors())


def get_by_id(item_id: int, orm_model: Type[AdvModel], session: Session):
    orm_item = session.query(orm_model).get(item_id)
    if orm_item is None:
        raise HTTPError(404, 'adv not found')
    return orm_item


class AdView(MethodView):

    def get(self, adv_id: int):
        with Session() as session:
            adv = get_by_id(adv_id, AdvModel, session)
            return jsonify({
                'adv': adv.title,
                'creation_time': adv.create_time.isoformat()
            })

    def post(self):
        json_data = request.json
        with Session() as session:
            try:
                new_ad = AdvModel(**validate(json_data, CreateAdvModel))
                session.add(new_ad)
                session.commit()
            except IntegrityError:
                raise HTTPError(409, 'title already exist')
            return jsonify({'status': 'ok', 'id': new_ad.id})

    def patch(self, adv_id: int):
        data_to_patch = validate(request.json, PatchAdvModel)
        with Session() as session:
            adv = get_by_id(adv_id, AdvModel, session)
            for field, value in data_to_patch.items():
                setattr(adv, field, value)
                session.commit()
                return jsonify({'status': 'ok'})

    def delete(self, adv_id: int):
        with Session() as session:
            adv = get_by_id(adv_id, AdvModel, session)
            session.delete(adv)
            session.commit()
            return jsonify({'status': 'ok'})


app.add_url_rule('/test/<int:adv_id>', view_func=AdView.as_view('advertisement_get'),
                 methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/test/', view_func=AdView.as_view('advertisements'), methods=['POST'])

app.run()
