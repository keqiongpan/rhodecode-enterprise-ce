import py.test

from rhodecode.lib.system_info import get_system_info


def test_system_info(app):
    info = get_system_info({})
    assert info['load']['value']['15_min'] != 'NOT AVAILABLE'


def test_system_info_without_psutil(monkeypatch, app):
    import rhodecode.lib.system_info
    monkeypatch.setattr(rhodecode.lib.system_info, 'psutil', None)
    info = get_system_info({})
    assert info['load']['value']['15_min'] == 'NOT AVAILABLE'
