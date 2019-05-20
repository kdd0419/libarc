#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import csv


# In[2]:


import libarc as arc


# In[3]:


dir(arc)


# In[4]:


help(arc.rank_me)


# In[5]:


from getpass import getpass


# In[6]:


user_name = input('input username > ')
user_pw = getpass('input PW > ')


# In[7]:


arc.user_login(user_name, user_pw, change_device_id=True)


# In[8]:


with open('songlist.json', 'r', encoding="utf-8") as songlist_f:
    songlist = json.loads(songlist_f.read())


# In[9]:


songlist = songlist['songs']
songlist


# In[10]:


song_id = []
for song in songlist:
    song_id.append({'id':song['id'],'name':song['title_localized']['en'], 'level':[diff['rating'] for diff in song['difficulties']]})


# In[11]:


song_id


# In[12]:


song_rlt=[]
diff = ['PAST', 'PRESENT', 'FUTURE']
clear_mode=['Track Lost', 'Track Complete (Normal Gauge)', 'Full Recall', 'Pure Memory', 'Track Complete (Easy Gauge)', 'Track Complete (Hard Gauge)']
for i in range(len(song_id)*3):
    score = arc.rank_me(song_id[i // 3]['id'], i % 3, 0, 0)['value']
    tmp_dic = {"song_name":song_id[i // 3]['name'], "difficulty": diff[i % 3], "level":song_id[i // 3]['level'][i % 3]}
    if len(score) <= 0:
        song_rlt.append(tmp_dic)
    else:
        tmp_dic['best_clear_type'] = clear_mode[score[0]['best_clear_type']]
        row = ['score', 'shiny_perfect_count', 'perfect_count', 'near_count','miss_count','rank']
        for r in row:
            tmp_dic[r] = score[0][r]
        song_rlt.append(tmp_dic)


# In[13]:


song_rlt


# In[14]:


with open('arcaea result.csv', 'w', newline="\n", encoding='utf-8') as csv_f:
    fieldnames = ['song_name', 'difficulty', 'level', 'score', 'shiny_perfect_count', 'perfect_count', 'near_count', 'miss_count', 'best_clear_type', 'rank']
    writer = csv.DictWriter(csv_f, fieldnames=fieldnames)
    writer.writeheader()
    for song in song_rlt:
        writer.writerow(song)


# In[ ]:




