from collections import defaultdict
from discord.ext import commands
from functools import partial, update_wrapper
from typing import Any, AnyStr, Dict, Callable, NoReturn, Set
import operator


# All tags that have been registered with the objects associated with those tags
__registered_tags__ = defaultdict(set)


def fetch_tags(*tags, operation: AnyStr = "and") -> Set:
    """ Fetches all objects that match the provided tags.

    By default only objects that have all requested tags will be selected. Setting
    the operation to "or" will cause the fetch to select all objects that match
    any of the requested tags. """
    operator_ = operator.and_ if operation == "and" else operator.or_
    tag_set = build_tag_set(*tags)
    if tag_set:
        matches = __registered_tags__[tag_set.pop()]
        for tag_name in tag_set:
            matches = operator_(matches, __registered_tags__[tag_name])
        return matches
    return set()


def build_tag_set(*tag_objects):
    tags = set()
    for tag_object in tag_objects:
        if isinstance(tag_object, str):
            tags.add(tag_object)
        elif hasattr(tag_object, "__iter__"):
            tags.update(tag_object)
        elif hasattr(tag_object, "tags"):
            tags.update(tag_object.tags)
    return tags


def assign_tags(obj: Any, *tags) -> NoReturn:
    """ Assigns an object the given tags. """
    for tag in tags:
        __registered_tags__[tag].add(obj)


def tag(*tags) -> Callable:
    """ Decorator that assigns tags to an object. """

    def decorator(obj: Any) -> Any:
        obj.tags = build_tag_set(tags)
        assign_tags(obj, *tags)
        return obj

    return decorator


class TaggableMeta(commands.CogMeta):
    """ Metaclass that allows for tags to be applied to instance attributes at instantiation.
    This is in contrast to the tags being applied to the unbound attributes. """

    def __call__(cls, *args, **kwargs):
        # Create the instance
        instance = super().__call__(*args, **kwargs)
        # Apply tags to the tagged attributes
        for attr_name, tags in cls.__tagged_attributes__.items():
            attr = getattr(instance, attr_name)
            assign_tags(attr, *tags)
        return instance

    @classmethod
    def __prepare__(metacls, name, bases):
        # Get the attributes of class
        attrs = super(TaggableMeta, metacls).__prepare__(name, bases)
        # Create the dictionary for tracking tagged attributes
        attrs["__tagged_attributes__"] = {}
        # Inherit tagged attribute
        for base in bases:
            if hasattr(base, "__tagged_attributes__"):
                attrs["__tagged_attributes__"].update(base.__tagged_attributes__)
        # Provide a tag decorator that is unique to the class
        attrs["tag"] = partial(metacls.class_tagger, attrs["__tagged_attributes__"])
        # Make the class decorator look like the global decorator
        update_wrapper(attrs["tag"], tag)
        return attrs

    @staticmethod
    def class_tagger(__tagged_attributes__: Dict, *tags) -> Callable:
        def decorator(obj: Any) -> Any:
            obj.tags = build_tag_set(tags)
            __tagged_attributes__[obj.__name__] = tags
            return obj

        return decorator
