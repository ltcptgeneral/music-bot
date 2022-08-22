import json

sample_json = """
{
	"guild":{
		"token": "",
		"prefix": "$",
		"roleid": 0,
		"username": "music-bot"
	},
}
"""

def load_config(path, config_vector):
	try:
		f = open(path, "r")
		config_vector.update(json.load(f))
		f.close()
		return 0
	except:
		f = open(path, "w")
		f.write(sample_json)
		f.close()
		return 1

def save_config(path, config_vector):
	f = open(path, "w")
	json.dump(config_vector, f, ensure_ascii=False, indent=4)
	f.close()
	return 0

def get_token(config_path):
	config_vector = {}
	success = load_config(config_path, config_vector)
	if success == 0:
		return config_vector["guild"]["token"]
	else:
		return None

def get_prefix(config_path):
	config_vector = {}
	success = load_config(config_path, config_vector)
	if success == 0:
		return config_vector["guild"]["prefix"]
	else:
		return None

def get_roleid(config_path):
	config_vector = {}
	success = load_config(config_path, config_vector)
	if success == 0:
		return config_vector["guild"]["roleid"]
	else:
		return None

def get_username(config_path):
	config_vector = {}
	success = load_config(config_path, config_vector)
	if success == 0:
		return config_vector["guild"]["username"]
	else:
		return None