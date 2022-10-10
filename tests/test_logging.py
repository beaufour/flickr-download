from flickr_download.logging_utils import _redact


def test_log_redaction() -> None:
    assert _redact("https://foo.com/?oauth_token=XYZ") == "https://foo.com/?oauth_token=***"
    assert (
        _redact("https://foo.com/?oauth_token=XYZ&foo=bar")
        == "https://foo.com/?oauth_token=***&foo=bar"
    )
    assert _redact("https://foo.com/&oauth_token=XYZ") == "https://foo.com/&oauth_token=***"
    assert (
        _redact("https://foo.com/?foo=bar&oauth_token=XYZ")
        == "https://foo.com/?foo=bar&oauth_token=***"
    )

    assert _redact("Nothing to see here!") == "Nothing to see here!"
    assert _redact("") == ""

    assert (
        _redact(
            "flickr_api.method_call:NO HIT for cache key:"
            "signature_method=HMAC-SHA1&oauth_token=jhasdkahsdkj&"
            "oauth_consumer_key=ajshdjahkgdajshk&method=flickr.photos.getInfo&"
            "photo_id=8864635232&api_key=asjhdakjhdkjashsdk&format=json&"
            "nojsoncallback=1&oauth_body_hash=jashdkashsdkjasda&"
            "oauth_signature_method=HMAC-SHA1"
        )
        == "flickr_api.method_call:NO HIT for cache key:"
        "signature_method=HMAC-SHA1&oauth_token=***&oauth_consumer_key=***&"
        "method=flickr.photos.getInfo&photo_id=8864635232&api_key=***&"
        "format=json&nojsoncallback=1&oauth_body_hash=***&"
        "oauth_signature_method=HMAC-SHA1"
    )
