# -*- coding: utf-8 -*-

# Copyright (C) 2016-2019 RhodeCode GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3
# (only), as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program is dual-licensed. If you wish to learn more about the
# RhodeCode Enterprise Edition, including its added features, Support services,
# and proprietary license terms, please see https://rhodecode.com/licenses/

import pickle
import pytest

from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from rhodecode.lib.jsonalchemy import (
    MutationDict, MutationList, MutationObj, JsonType)


@pytest.fixture()
def engine():
    return create_engine('sqlite://')


@pytest.fixture()
def session(engine):
    return sessionmaker(bind=engine)()


def test_mutation_dict_is_picklable():
    mutation_dict = MutationDict({'key1': 'value1', 'key2': 'value2'})
    dumped = pickle.dumps(mutation_dict)
    loaded = pickle.loads(dumped)
    assert loaded == mutation_dict


def test_mutation_list_is_picklable():
    mutation_list = MutationList(['a', 'b', 'c'])
    dumped = pickle.dumps(mutation_list)
    loaded = pickle.loads(dumped)
    assert loaded == mutation_list


def test_mutation_dict_with_lists_is_picklable():
    mutation_dict = MutationDict({
        'key': MutationList(['values', MutationDict({'key': 'value'})])
    })
    dumped = pickle.dumps(mutation_dict)
    loaded = pickle.loads(dumped)
    assert loaded == mutation_dict


def test_mutation_types_with_nullable(engine, session):
    # TODO: dan: ideally want to make this parametrized python => sql tests eg:
    # (MutationObj, 5) => '5'
    # (MutationObj, {'a': 5}) => '{"a": 5}'
    # (MutationObj, None) => 'null' <- think about if None is 'null' or NULL

    Base = declarative_base()

    class DummyModel(Base):
        __tablename__ = 'some_table'
        name = Column(String, primary_key=True)
        json_list = Column(MutationList.as_mutable(JsonType('list')))
        json_dict = Column(MutationDict.as_mutable(JsonType('dict')))
        json_obj = Column(MutationObj.as_mutable(JsonType()))

    Base.metadata.create_all(engine)

    obj_nulls = DummyModel(name='nulls')
    obj_stuff = DummyModel(
        name='stuff', json_list=[1,2,3], json_dict={'a': 5}, json_obj=9)

    session.add(obj_nulls)
    session.add(obj_stuff)
    session.commit()
    session.expire_all()

    assert engine.execute(
        "select * from some_table where name = 'nulls';").first() == (
        (u'nulls', None, None, None)
    )
    ret_nulls = session.query(DummyModel).get('nulls')
    assert ret_nulls.json_list == []
    assert ret_nulls.json_dict == {}
    assert ret_nulls.json_obj is None

    assert engine.execute(
        "select * from some_table where name = 'stuff';").first() == (
        (u'stuff', u'[1, 2, 3]', u'{"a": 5}', u'9')
    )
    ret_stuff = session.query(DummyModel).get('stuff')
    assert ret_stuff.json_list == [1, 2, 3]
    assert ret_stuff.json_dict == {'a': 5}
    assert ret_stuff.json_obj == 9
