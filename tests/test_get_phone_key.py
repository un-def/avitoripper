import pytest

from avitoripper import get_phone_key


@pytest.mark.parametrize('item_id,item_phone,expected', [
    ('1874436382', (
        'aff33f947ce76786b3bae3a6207655m3d4f86268a4d811336eaca5cmbc52'
        'caa63811mbffm5748f3md8787em37006afea23bm955'
    ), '930f2d858bb2a83f2a83eaa39c66b326'),
    ('1965371073', (
        's727a4b9630ba323097e7d10011c60afbds4f1f7cb85b640e6s36e046f585'
        'c701fs5db1a04c14003d7479sb327abb36ab4472'
    ), '7a9030e116f4fbb030f50514434b7ba4'),
    ('1907246894', (
        'f649757b359ce952ad1f778al667l251b159834ed99250802162al0de638l'
        'd29l012380l8a877f7da6594c9d3b957c46576ea2'
    ), '87764d9c5e03d062b9495066f975e217'),
    ('1806897741', (
        'ya57c6be4661c37by2bffebf31c424cd888f03571db865af6b4b6ba508by6'
        '17f30ya88adc4241137beyafbfb74c1c64y3b6d75'
    ), 'ace632ffc48f5d6f4b06faa417af4c3d'),
])
def test_get_phone_key(item_id, item_phone, expected):
    assert get_phone_key(item_id, item_phone) == expected
