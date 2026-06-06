from datetime import datetime
from functools import cache
from typing import Any

from polyfactory.exceptions import ParameterException
from polyfactory.factories import BaseFactory
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.factories.typed_dict_factory import TypedDictFactory
from polyfactory.field_meta import FieldMeta


class FakeFactory:
    @classmethod
    @cache
    def _create_factory[T](
        cls,
        factory_class: type[BaseFactory],
        model: type[T],
    ) -> type[BaseFactory]:
        class Factory(factory_class):
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

                    return FakeFactory._create_factory(
                        factory_class,
                        annotation,
                    ).build(**kwargs)

        return Factory

    @classmethod
    def model[T](
        cls,
        model: type[T],
        **kwargs: Any,
    ) -> T:
        return cls._create_factory(
            ModelFactory,
            model,
        ).build(**kwargs)

    @classmethod
    def typed_dict[T](
        cls,
        model: type[T],
        **kwargs: Any,
    ) -> T:
        return cls._create_factory(
            TypedDictFactory,
            model,
        ).build(**kwargs)

    @classmethod
    def typed_dicts[T](
        cls,
        model: type[T],
        count: int,
        **kwargs: Any,
    ) -> list[T]:
        return [cls.typed_dict(model, **kwargs) for _ in range(count)]
