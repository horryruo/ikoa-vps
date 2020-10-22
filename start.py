from loadini import read_config
import os
def start():
    conf_data = read_config()
    cmd = 'bash start.sh {} {} {} {} {}'.format(conf_data['serial_code'],conf_data['team_drive_id'],conf_data['merge_bool'],conf_data['output_filename'],conf_data['runport'])
    #print(cmd)
    os.system(cmd)
    #cmd = ''

if __name__ == '__main__':
    start()