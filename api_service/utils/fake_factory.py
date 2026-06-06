from __future__ import annotations

from datetime import datetime
from typing import Any, TypeVar

from polyfactory.exceptions import ParameterException
from polyfactory.factories import BaseFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.factories.typed_dict_factory import TypedDictFactory
from polyfactory.field_meta import FieldMeta

T = TypeVar("T")

FactoryT = type[BaseFactory]
FactoryKey = tuple[FactoryT, type[Any]]


class FakeFactory:
    _cache: dict[FactoryKey, FactoryT] = {}

    @classmethod
    def _create_factory(
        cls,
        factory_class: FactoryT,
        model: type[Any],
    ) -> FactoryT:
        key: FactoryKey = (factory_class, model)

        if key in cls._cache:
            return cls._cache[key]

        class Factory(factory_class):  # type: ignore[valid-type, misc]
            __model__ = model

            @classmethod
            def get_mock_value(cls, annotation: Any) -> Any:
                if isinstance(annotation, type) and issubclass(annotation, datetime):
                    value: datetime = super().get_mock_value(datetime)
                    return value.astimezone()

                return super().get_mock_value(annotation)

            @classmethod
            def get_field_value(
                cls,
                field_meta: FieldMeta,
                field_build_parameters: Any = None,
                *args: Any,
                **kwargs: Any,
            ) -> Any:
                try:
                    return super().get_field_value(
                        field_meta,
                        field_build_parameters,
                        *args,
                        **kwargs,
                    )
                except ParameterException:
                    annotation = field_meta.annotation

                    if not isinstance(annotation, type):
                        raise

                    nested_factory = FakeFactory._create_factory(
                        factory_class,
                        annotation,
                    )
                    return nested_factory.build(**kwargs)

        cls._cache[key] = Factory
        return Factory

    @classmethod
    def model(
        cls,
        model: type[T],
        **kwargs: Any,
    ) -> T:
        factory = cls._create_factory(ModelFactory, model)
        return factory.build(**kwargs)

    @classmethod
    def typed_dict(
        cls,
        model: type[T],
        **kwargs: Any,
    ) -> T:
        factory = cls._create_factory(TypedDictFactory, model)
        return factory.build(**kwargs)

    @classmethod
    def typed_dicts(
        cls,
        model: type[T],
        count: int,
        **kwargs: Any,
    ) -> list[T]:
        return [cls.typed_dict(model, **kwargs) for _ in range(count)]