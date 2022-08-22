import json

sample_json = """
{
	"guild":{
		"token": "",
		"prefix": "?",
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