import requests


data = requests.post('http://127.0.0.1:5000/test/',
                     json={
                         'title': 'News',
                         'owner': 'MTV'
                     })

# get_adv = requests.get('http://127.0.0.1:5000/test/1')
#
# patch_adv = requests.patch('http://127.0.0.1:5000/test/1', json={'title': 'News from Russia'})
#
# del_adv = requests.delete('http://127.0.0.1:5000/test/1')

print(data.text)
print(data.status_code)

# print(get_adv.text)
# print(get_adv.status_code)
#
# print(patch_adv.text)
# print(patch_adv.status_code)
#
# print(del_adv.text)
# print(del_adv.status_code)
