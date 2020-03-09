# Noteton
telegram bot @noteton_bot

# Installation:
1. Set up packages from requirement
2. Create `config.py` in root folder, config has 2 variables:
```python
token = ''  # string, telegram bot token
god_chat_id = ''  # string, telegram id of admin
```

Bot works with AWS DynamoDB, so, machine with bot should has access to DynamoDB (see AWS instructions, the easiest way is run on EC@ instance with DynamoBD full access role).

Database should has 3 tables: 
* NotetonUser with key `user_id`
* NotetonList with key `user_id` and sorted key `list_id`
* NotetonListItem with key `list_id` and sorted key `item_id`

Versions:
* MVP (v0.01) - 9th march, minimum functional, close testing
* Photon (v0.1) - 13th april, user-friendly improvements: user guide, hints, default behaviour, limits


