from app.scraping.proxy import ProxyPool


def test_gateway_mode_returns_same_endpoint():
    pool = ProxyPool(gateway="http://gw:8000")
    assert pool.enabled
    assert pool.get_proxy() == "http://gw:8000"
    # mark_bad на шлюз не влияет
    pool.mark_bad("http://gw:8000")
    assert pool.get_proxy() == "http://gw:8000"


def test_no_proxy_when_unconfigured():
    pool = ProxyPool()
    assert not pool.enabled
    assert pool.get_proxy() is None


def test_list_rotation_round_robin():
    pool = ProxyPool(proxies=["http://a", "http://b", "http://c"])
    got = [pool.get_proxy() for _ in range(4)]
    assert got == ["http://a", "http://b", "http://c", "http://a"]


def test_bad_proxy_is_skipped_during_cooldown():
    pool = ProxyPool(proxies=["http://a", "http://b"], cooldown_seconds=999)
    pool.mark_bad("http://a")
    # «a» на cooldown — должны получать только «b»
    assert pool.get_proxy() == "http://b"
    assert pool.get_proxy() == "http://b"
