from webapp import loadini

def start():
    conf_data = loadini.read_config()
    cmd = 'ts bash start.sh {} {} {} {} {} {}'.format(conf_data['serial_code'],conf_data['team_drive_id'],conf_data['sa_1'],conf_data['sa_1'],conf_data['merge_bool'],conf_data['output_filename'])
    #print(cmd)
    os.system(cmd)
    #cmd = ''

if __name__ == '__main__':
    start()