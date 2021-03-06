from bisect import bisect

from collections import OrderedDict
from django.core.cache import cache

from dbsettings.models import Setting

__all__ = ['get_all_settings', 'get_setting', 'get_setting_storage',
           'register_setting', 'unregister_setting', 'set_setting_value']


_settings = OrderedDict()


def _get_cache_key(module_name, class_name, attribute_name):
    return '.'.join(['dbsettings', module_name, class_name, attribute_name])


def get_all_settings():
    return _settings


def get_app_settings(app_label):
    return [p for p in _settings if app_label == p.module_name.split('.')[-2]]


def get_setting(module_name, class_name, attribute_name):
    return _settings[module_name, class_name, attribute_name]


def get_setting_storage(module_name, class_name, attribute_name):
    key = _get_cache_key(module_name, class_name, attribute_name)
    storage = cache.get(key)
    if storage is None:
        try:
            storage = Setting.objects.get(
                module_name=module_name,
                class_name=class_name,
                attribute_name=attribute_name,
            )
        except Setting.DoesNotExist:
            setting_object = get_setting(module_name, class_name, attribute_name)
            storage = Setting(
                module_name=module_name,
                class_name=class_name,
                attribute_name=attribute_name,
                value=setting_object.default,
            )
        cache.set(key, storage)
    return storage


def register_setting(setting):
    if setting.key not in _settings:
        _settings[setting.key]=setting


def unregister_setting(setting):
    if setting.key in _settings and _settings[setting.key] is setting:
        del _settings[setting.key]


def set_setting_value(module_name, class_name, attribute_name, value):
    setting = get_setting(module_name, class_name, attribute_name)
    storage = get_setting_storage(module_name, class_name, attribute_name)
    storage.value = setting.get_db_prep_save(value)
    storage.save()
    key = _get_cache_key(module_name, class_name, attribute_name)
    cache.delete(key)
