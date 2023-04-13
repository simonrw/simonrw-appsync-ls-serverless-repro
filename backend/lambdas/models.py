import json
import logging as log
from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeMeta, declarative_base, QueryableAttribute

from lambdas.utils import str_utils, common

Base: DeclarativeMeta = declarative_base()


def _prepend_path(path, field_name):
    field_name = field_name.lower()
    if field_name.split(".", 1)[0] == path:
        return field_name
    if len(field_name) == 0:
        return field_name
    if field_name[0] != ".":
        field_name = f".{field_name}"
    field_name = f"{path}{field_name}"
    return field_name


class DbModel(Base):
    __abstract__ = True

    def model_to_dict(self, show: list = None,  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
                      _hide: list = None,
                      _path: str = None,
                      camel_case: bool = True,
                      serialize: bool = True,
                      type_name: str = None):
        """Return a dictionary representation of this model."""

        show = show or []
        _hide = _hide or []

        hidden = self._hidden_fields if hasattr(self, "_hidden_fields") else []
        default = self._default_fields if hasattr(self, "_default_fields") else []
        default.extend(['id', 'created', 'modified'])

        if not _path:
            _path = getattr(self, '__tablename__').lower()
            _hide[:] = [_prepend_path(_path, x) for x in _hide]
            show[:] = [_prepend_path(_path, x) for x in show]

        columns = getattr(self, '__table__').columns.keys()
        relationships: list[str] = getattr(self, '__mapper__').relationships.keys()
        properties = dir(self)

        ret_data: dict = {'__typename': type_name} if type_name is not None else {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = f"{_path}.{key}"
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                result_key = str_utils.convert_snake_to_camel_case(key) if camel_case else key
                value = getattr(self, key)
                if serialize is True:
                    value = common.serialize_object(value)
                ret_data[result_key] = value

        for key in relationships:
            if key.startswith("_"):
                continue
            check = f"{_path}.{key}"
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                result_key: str = str_utils.convert_snake_to_camel_case(key) if camel_case else key
                _hide.append(check)
                is_list = getattr(self, '__mapper__').relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if getattr(self, '__mapper__').relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all()
                    ret_data[result_key] = []
                    for item in items:
                        ret_data[result_key].append(
                            item.model_to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=f"{_path}.{key.lower()}"
                            )
                        )
                else:
                    relation = getattr(self, '__mapper__').relationships[key]
                    if (
                        relation.query_class is not None
                        or relation.instrument_class is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[result_key] = item.model_to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=f"{_path}.{key.lower()}",
                            )
                        else:
                            ret_data[result_key] = None
                    else:
                        ret_data[result_key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not isinstance(attr, (property, QueryableAttribute)):
                continue
            check = f"{_path}.{key}"
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                result_key = str_utils.convert_snake_to_camel_case(key) if camel_case else key
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[result_key] = val.model_to_dict(
                        show=list(show),
                        _hide=list(_hide),
                        _path=f"{_path}.{key.lower()}"
                    )
                else:
                    try:
                        ret_data[result_key] = json.loads(json.dumps(val))
                    except Exception:  # pylint: disable=broad-except
                        log.error("Could not serialise the field %s", check)

        return ret_data


class UserAccount(DbModel):
    __tablename__ = "user_account"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_name = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    def to_dict(self, show: list = None):
        show = show if show is not None else ['user_name',
                                              'name',
                                              'email',
                                              'organisation',
                                              'organisation.name',
                                              'organisation.display_name']
        return super().model_to_dict(show)
