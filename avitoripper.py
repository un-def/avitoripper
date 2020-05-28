import io
import re
import sys
from base64 import b64decode
from itertools import chain, islice
from typing import Dict
from urllib.parse import urljoin

import requests
from lxml import etree
from PIL import Image
from tesserocr import image_to_text


USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0')
BASE_URL = 'https://www.avito.ru/'
# An URL to get phone number image.
PHONE_URL = urljoin(BASE_URL, '/items/phone/')
# A name of a query parameter for `PHONE_URL`.
PHONE_URL_KEY_PARAM = 'pkey'


# A text in <script> elements used to find the proper one.
JS_AVITO_ITEM_MARKER = 'avito.item'
# This regex is deliberately simple and cannot properly parse
# (qoutes, escapes, etc.) any field. We are only interested in a few of them.
JS_AVITO_ITEM_ASSIGN_REGEX = re.compile(
    r"""avito\.item\.(?P<key>[a-zA-Z0-9_]+) *= *['"]?(?P<value>.*?)['"]?;"""
)


ITEM_PHONE_SPLIT_REGEX = re.compile(r'[0-9a-f]+')


def get_phone_key(item_id: str, item_phone: str) -> str:
    """
    Deobfuscate phone key (`pkey` query parameter).

    Original code, slightly reformatted:

    avito.utils.phoneDemixer = function (e, t) {
        if (!t) return '';
        var i,
            o = t.match(/[0-9a-f]+/g),
            n = (e % 2 == 0 ? o.reverse()  : o).join(''),
            r = n.length,
            a = '';
        for (i = 0; i < r; ++i) i % 3 == 0 && (a += n.substring(i, i + 1));
        return a
    }
    """
    iterable = ITEM_PHONE_SPLIT_REGEX.findall(item_phone)
    if not int(item_id) % 2:
        iterable = reversed(iterable)
    return ''.join(islice(chain.from_iterable(iterable), None, None, 3))


def get_avito_item(url: str, *, session: requests.Session) -> Dict:
    response = session.get(url, stream=True)
    response.raise_for_status()
    tree = etree.parse(response.raw, parser=etree.HTMLParser())
    for el in tree.xpath(f'//script[contains(., "{JS_AVITO_ITEM_MARKER}")]'):
        found = JS_AVITO_ITEM_ASSIGN_REGEX.findall(el.text)
        if found:
            return dict(found)
    raise ValueError('avito.item not found')


def unicode_unescape(string: str) -> str:
    return string.encode().decode('unicode-escape', errors='ignore')


def get_phone(
    item_id: str, phone_key: str, *, session: requests.Session,
) -> str:
    response = session.get(
        urljoin(PHONE_URL, item_id),
        params={PHONE_URL_KEY_PARAM: phone_key},
    )
    response.raise_for_status()
    image_data_url = response.json()['image64']
    assert image_data_url.startswith('data:')
    _, _, image_data = image_data_url.partition(',')
    with io.BytesIO(b64decode(image_data.strip())) as image_fo:
        with Image.open(image_fo) as image:
            phone = image_to_text(image).strip()
    phone_parts = list(filter(str.isdigit, phone))
    if phone_parts[0] == '8':
        phone_parts[0] = '+7'
    return ''.join(phone_parts)


def grab(__url_or_item_id: str) -> Dict:
    if __url_or_item_id.startswith('http'):
        url = __url_or_item_id
    elif __url_or_item_id.isdigit():
        url = urljoin(BASE_URL, __url_or_item_id)
    else:
        raise ValueError('invalid URL or item ID')
    with requests.Session() as session:
        session.headers = {'User-Agent': USER_AGENT}
        avito_item = get_avito_item(url, session=session)
        assert 'id' in avito_item
        assert 'phone' in avito_item
        item_id = avito_item['id']
        phone_key = get_phone_key(item_id, avito_item['phone'])
        phone = get_phone(item_id, phone_key, session=session)
    url = avito_item.get('url', '')
    if url and url.startswith('/'):
        url = urljoin(BASE_URL, url)
    image_url = avito_item.get('image', '')
    if image_url and image_url.startswith('/'):
        image_url = urljoin(BASE_URL, image_url)
    return {
        'id': item_id,
        'url': url,
        'image_url': image_url,
        'title': unicode_unescape(avito_item.get('title', '')),
        'location': unicode_unescape(avito_item.get('location', '')),
        'price': avito_item.get('price', ''),
        'phone': phone,
    }
    return


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: avitoripper URL or avitoripper ITEM_ID')
    info = grab(sys.argv[1])
    for key, value in info.items():
        print(f'{key}: {value}')
