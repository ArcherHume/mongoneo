_class_registry_cache = {}
_field_list_cache = []


def _import_class(cls_name):
    """Cache mechanism for imports.

    Due to complications of circular imports mongoneo needs to do lots of
    inline imports in functions.  This is inefficient as classes are
    imported repeated throughout the mongoneo code.  This is
    compounded by some recursive functions requiring inline imports.

    :mod:`mongoneo.common` provides a single point to import all these
    classes.  Circular imports aren't an issue as it dynamically imports the
    class when first needed.  Subsequent calls to the
    :func:`~mongoneo.common._import_class` can then directly retrieve the
    class from the :data:`mongoneo.common._class_registry_cache`.
    """
    if cls_name in _class_registry_cache:
        return _class_registry_cache.get(cls_name)

    doc_classes = (
        "Document",
        "DynamicEmbeddedDocument",
        "EmbeddedDocument",
        "MapReduceDocument",
    )

    # Field Classes
    if not _field_list_cache:
        from mongoneo.fields import __all__ as fields

        _field_list_cache.extend(fields)
        from mongoneo.base.fields import __all__ as fields

        _field_list_cache.extend(fields)

    field_classes = _field_list_cache

    deref_classes = ("DeReference",)

    if cls_name == "BaseDocument":
        from mongoneo.base import document as module

        import_classes = ["BaseDocument"]
    elif cls_name in doc_classes:
        from mongoneo import document as module

        import_classes = doc_classes
    elif cls_name in field_classes:
        from mongoneo import fields as module

        import_classes = field_classes
    elif cls_name in deref_classes:
        from mongoneo import dereference as module

        import_classes = deref_classes
    else:
        raise ValueError("No import set for: %s" % cls_name)

    for cls in import_classes:
        _class_registry_cache[cls] = getattr(module, cls)

    return _class_registry_cache.get(cls_name)
