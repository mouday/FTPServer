
# 客户端实现

import socket
import os
import json
import hashlib

class FtpClient(object):
    def __init__(self,):
        self.client = socket.socket()

    def connect(self, ip, port):
        self.client.connect((ip, port))

    def login(self):
        """用户登录"""
        name = input("请输入用户名：").strip()
        password = input("请输入密码：").strip()
        infos = {
            "action": "login",
            "name": name,
            "password": password
        }

        # 发送用户信息进行认证
        self.client.send(json.dumps(infos).encode("utf-8"))

        # 判断返回信息
        res = self.client.recv(1024).decode("utf-8")
        if res == "0":
            print("登陆成功")
            self.interactive()
        else:
            print("登陆失败")

    def interactive(self):
        """用户交互"""
        while True:
            cmd = input(">>")
            # 输入为空，继续等待用户输入
            if len(cmd)==0 :continue
            action = cmd.split(" ")[0]

            # 反射，通过函数名字符串获取函数地址，便于扩展
            if hasattr(self, "%s" % action):
                func = getattr(self, "%s" % action)
                func(cmd)
            else:
                self.help()

    def put(self, *args):
        """客户端，发送文件"""
        cmd_split = args[0].split(" ")
        if len(cmd_split)>1:
            filename = cmd_split[1]

            # 判断文件是否存在，存在则继续
            if os.path.isfile(filename):
                size = os.stat(filename).st_size  # 获取文件大小
                msg_dct = {
                    "action": "put",
                    "filename": filename,
                    "size": size,
                    "override": True
                }

                # 第一次发送操作文件信息
                self.client.send(json.dumps(msg_dct).encode("utf-8"))

                # 确认接收，防止粘包，确认服务器空间是否足够
                server_response = self.client.recv(1024).decode("utf-8")
                if server_response == "0":
                    print("空间足够")
                else:
                    print("空间不足")
                    return  # 中断操作

                # 接着发送文件内容
                m = hashlib.md5()
                f = open(filename, "rb")
                send_len = 0
                for line in f:
                    self.client.send(line)
                    m.update(line)
                    send_len+=len(line)
                    # print("传输进度：{} %".format(round(send_len/size, 2)*100))
                f.close()

                # 可以增加MD5校验
                self.client.send(m.hexdigest().encode("utf-8"))
                res = self.client.recv(1024).decode("utf-8")
                if res =="0":
                    print("文件传输成功")
                else:
                    print("文件传输失败")
            else:
                print("文件不存在 %s" % filename)

    def get(self, *args):
        """客户端，接收文件"""
        cmd_split = args[0].split(" ")
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            msg_dct = {
                "action": "get",
                "filename": filename
            }

            # 第一次发送操作文件信息
            self.client.send(json.dumps(msg_dct).encode("utf-8"))

            # 接收文件状态，是否存在和文件大小
            server_response = self.client.recv(1024)
            server_dct= json.loads(server_response.decode("utf-8"))

            if server_dct["isfile"]:  # 文件存在
                self.client.send(b"200 ok")  # 确认接收

                # 接收文件内容
                m = hashlib.md5()
                f = open(filename, "wb")
                data_size = server_dct["size"]
                received_size = 0
                while received_size < data_size:
                    # 精确控制接收数据大小
                    if data_size-received_size>1024:
                        size = 1024
                    else:
                        size = data_size-received_size
                    data = self.client.recv(size)

                    f.write(data)
                    m.update(data)
                    received_size += len(data)
                    # print("传输进度：{} %".format(int(round(received_size / data_size, 2) * 100)))
                else:
                    f.close()

                    # 接收MD5校验
                    received_md5 = self.client.recv(1024).decode("utf-8")
                    if m.hexdigest() == received_md5:
                        print("文件下载成功")
                        self.client.send("0".encode("utf-8"))
                    else:
                        print("文件下载出错")
                        self.client.send("-1".encode("utf-8"))
            else:
                print("文件不存在")

    def cd(self, *args):
        """客户端，改变文件目录"""
        cmd_split = args[0].strip().split(" ")
        if len(cmd_split) > 1:
            dirname = cmd_split[1]

            msg_dct = {
                "action": "cd",
                "dirname": dirname
            }

            # 第一次发送操作文件信息
            self.client.send(json.dumps(msg_dct).encode("utf-8"))

            # 接收文件状态，是否改变成功
            server_response = self.client.recv(1024)
            server_dct = json.loads(server_response.decode("utf-8"))

            print(server_dct["current"])

    def ls(self, *args):
        """客户端，查看文件目录"""
        msg_dct = {
            "action": "ls"
        }
        # 第一次发送操作文件信息
        self.client.send(json.dumps(msg_dct).encode("utf-8"))

        # 接收文件状态，是否改变成功
        server_response = self.client.recv(1024)
        server_dct = json.loads(server_response.decode("utf-8"))

        print(server_dct["list"])

    def pwd(self, *args):
        """客户端，查看当前路径"""
        msg_dct = {
            "action": "pwd"
        }
        # 第一次发送操作文件信息
        self.client.send(json.dumps(msg_dct).encode("utf-8"))

        # 接收文件状态，是否改变成功
        server_response = self.client.recv(1024)
        server_dct = json.loads(server_response.decode("utf-8"))

        print(server_dct["current"])

    def mkdir(self, *args):
        """客户端，创建文件目录"""
        cmd_split = args[0].strip().split(" ")
        if len(cmd_split) > 1:
            dirname = cmd_split[1]
            msg_dct = {
                "action": "mkdir",
                "dirname": dirname
            }
            # 第一次发送操作文件信息
            self.client.send(json.dumps(msg_dct).encode("utf-8"))

            # 接收文件状态，是否创建成功
            server_response = self.client.recv(1024)
            server_dct = json.loads(server_response.decode("utf-8"))

            print(server_dct["current"])

    def help(self):
        """帮助信息"""
        msg="""
        ls
        pwd
        cd ../..
        mkdir
        get filename
        put filename
        """
        print(msg)

def run():
    """启动客户端"""
    myftp = FtpClient()
    myftp.connect("localhost", 6969)
    myftp.login()

if __name__ =="__main__":
    run()