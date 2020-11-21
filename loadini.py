import configparser
import os
 
def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini", encoding='utf-8')
    conf_data = {}
    drive = config['default']['usedrive']
    conf_data['drive'] = drive
    destination_path = config['default']['destination_path']
    conf_data['destination_path'] = destination_path
    log_path = config['default']['log_path']
    conf_data['log_path'] = log_path
    adminUser = config['default']['adminUser']
    conf_data['adminUser'] = adminUser
    adminPassword = config['default']['adminPassword']
    conf_data['adminPassword'] = adminPassword
    merge_bool = config['default']['merge_bool']
    conf_data['merge_bool'] = merge_bool
    serial_code = config['default']['serial_code']
    conf_data['serial_code'] = serial_code
    monthly_only = config['default']['monthly_only']
    conf_data['monthly_only'] = monthly_only
    output_filename = config['default']['output_filename']
    conf_data['output_filename'] = output_filename
    runport = config['default']['runport']
    conf_data['runport'] = runport
    secret_key = config['default']['secret_key']
    if secret_key == '':
        secret_key = os.urandom(24)
        config.set("default", "secret_key", str(secret_key))
        with open("config.ini", "w+") as f:
            config.write(f)
    conf_data['secret_key'] = secret_key
    
    team_drive_id = config['rclone_conf_gd']['team_drive_id']
    conf_data['team_drive_id'] = team_drive_id
    down_time = config['default']['down_time']
    conf_data['down_time'] = down_time
    accounts = config['default']['accounts']
    conf_data['accounts'] = accounts

    
   

    return conf_data
if __name__ == '__main__':
    conf_data = read_config()
    print(conf_data)
