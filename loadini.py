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
    secret_key = config['default']['secret_key']
    if secret_key == '':
        secret_key = os.urandom(24)
        config.set("default", "secret_key", str(secret_key))
        with open("config.ini", "w+") as f:
            config.write(f)
    conf_data['secret_key'] = secret_key
    if drive == 'gd':
        team_drive_id = config['rclone_conf_gd']['team_drive_id']
        conf_data['team_drive_id'] = team_drive_id
        sa_1 = config['rclone_conf_gd']['sa_1']
        conf_data['sa_1'] = sa_1
        sa_2 = config['rclone_conf_gd']['sa_2']
        conf_data['sa_2'] = sa_2

    elif drvie == 'od':
        od_conf = config['rclone_conf_od']['rclone_conf']
        conf_data['od_conf'] = od_conf
    else:
        print('配置文件错误')

    return conf_data
if __name__ == '__main__':
    conf_data = read_config()
    print(conf_data)
