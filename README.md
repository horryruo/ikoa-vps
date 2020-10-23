# ikoa-vps   beta
[![BSD-3](https://img.shields.io/badge/LICENSE-BSD3-brightgreen.svg)](https://github.com/horryruo/multi-bot/blob/master/LICENSE)

**由项目ikoa-web衍生而来，用于部署于vps上以供下载。**  

## 免责声明：本代码仅用于学习，下载后请勿用于商业用途，本人对此有最终解释权。
## Disclaimer: This code is only for learning, please do not use it for commercial purposes after downloading, I have the final right of interpretation.
## Tips
1、由于本人只略懂python，其他的docker、shell没接触过，因此无法针对vps环境对shell、js等文件做出修改，只能大致更改到可以使用的程度（有小bug也不奇怪）

2、由于存在隐私序列码等，请clone后只pull而不push，本项目已对敏感文件进行gitgnore处理，但ikoa自带的config由于特殊原因还是不在名单里，请自行注意，由于操作不当导致序列码泄露的，本项目概不负责。

3、本项目只经过少量测试，且本人也是菜鸟，有bug在所难免。出现bug如果有能力的可以自己修修，更可以直接提issue并把问题怎么解决贴出来。而只提无意义问题的概不回复。大bug且我会修的话会尽快修复。。


## install
  由于本人能力有限，不能实现完全自动化，部分文件任需手动，
  以下过程需要一定的linux基础，不懂的自行谷歌(⊙o⊙)
  
1、Python 3.6+ is Required  

2、`git clone https://github.com/horryruo/ikoa-vps.git && chmod +x ikoa-vps` 

3、`cd ikoa-vps`  

4、`pip3 install -r requirements.txt`  

5、`cp config.ini.example config.ini` 

6、install rclone `curl https://rclone.org/install.sh | sudo bash`

7、 确保你的ikoa可以使用，本程序默认使用64位ikoa，如要使用32位，把fanza文件夹"iKOA"重命名，然后把"iKOA_32位"重命名为"iKOA"(区分大小写),且先安装ikoa所需依赖（32位glibc 2.15，64位glibc 2.28，请自行谷歌如何安装），成功能单独启动iKOA才进行下一步。

8、原程序带有unix软件包，先自行安装：centos: `yum -y install epel-release && yum -y install moreutils`  debian:`apt-get install moreutils`

9、配置config.ini,内有说明

10、原sa文件，请自行在fanza文件夹创建两个文件service_account_1.json、service_account_2.json，并分别把sa全部内容复制进去即可。（sa文件也不会参与git同步）

11、确保配置完毕，即可在ikoa-vps目录下，创建screen，然后运行`python3 start.py`,接着就可以在浏览器输入你的vps ip：端口，看到熟悉的页面

12、可使用nginx/caddy反代127.0.0.1:端口 即可实现https访问

13、如若配置失败，或者运行失败需要重新运行，往往会被占用端口，使用命令`lsof -i:端口`可查看所有占用端口程序，再使用`kill -9 pid`结束所有进程再开启服务。


### 上传到onedrive
目前为测试版，请在本地rclone配置好onedrive配置文件（自行谷歌），然后把除名字外全部内容复制到rclone_3.conf,注意不要删掉原来到[DRIVE]标题，此为程序内置名字，更改后无法上传。

