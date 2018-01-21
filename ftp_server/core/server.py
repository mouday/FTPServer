
# 支持多用户的服务器

import socketserver
import json
import hashlib
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(BASE_DIR)

from core import user_manager as users


# 确定文件路径
users_path = users.users_path
home = r"../files/"

# 实现服务器端功能函数
class MyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """服务器端，数据接收入口"""
        while True:
            try:
                self.data = self.request.recv(1024)  # 接收
                print("客户端地址：", self.client_address)
                print("客户端信息：", self.data)

                cmd_dct = json.loads(self.data.decode("utf-8"))
                action = cmd_dct["action"]
                if hasattr(self, action):
                    func = getattr(self, action)
                    func(cmd_dct)

            except ConnectionResetError as e:
                print(e)
                break

    def login(self, *args):
        """服务器端，登陆接口"""
        cmd_dct = args[0]
        user_path = os.path.join(users_path, cmd_dct["name"]+".json")
        print(user_path)

        # 验证用户是否存在
        if os.path.isfile(user_path):
            user = json.load(open(user_path, "r"))

            if cmd_dct["password"] == user["password"]:
                self.request.send("0".encode("utf-8"))
                print("登陆成功")

                # 准备用户目录
                self.current = user["name"]
                self.username = user["name"]
                current_path = os.path.join(home, self.current)
                if not os.path.exists(current_path):
                    os.mkdir(current_path)

                return  # 登陆成功返回
            else:
                print("密码错误")
        else:
            print("用户不存在")
        self.request.send("-1".encode("utf-8"))


    def put(self, *args):
        """服务器端，接收文件"""
        cmd_dct= args[0]
        current_path = os.path.join(home, self.current)
        filename = os.path.join(current_path, cmd_dct["filename"])
        filesize = cmd_dct["size"]

        # 验证用户空间是否足够 确认接收
        userinfo = users.getinfo(self.username)
        if userinfo["total_size"] - userinfo["used_size"] > filesize:
            self.request.send("0".encode("utf-8"))
            print("空间足够")
        else:
            self.request.send("-1".encode("utf-8"))
            print("空间不足")
            return

        # 接收文件内容
        if os.path.isfile(filename):
            f = open("new_"+filename, "wb")
        else:
            f = open(filename, "wb")
        received_size = 0
        m = hashlib.md5()
        while received_size < filesize:
            # 精确控制接收数据大小
            if filesize - received_size > 1024:
                size = 1024
            else:
                size = filesize - received_size
            data = self.request.recv(size)

            f.write(data)
            m.update(data)
            received_size += len(data)
        else:
            f.close()
            # 增加已经使用的空间
            users.add_used_size(self.username, received_size)

            # MD5值校验
            received_md5 = self.request.recv(1024).decode("utf-8")
            if m.hexdigest() == received_md5:
                print("文件上传成功")
                self.request.send("0".encode("utf-8"))
            else:
                print("文件上传出错")
                self.request.send("-1".encode("utf-8"))

    def get(self, *args):
        """服务器端，发送文件"""
        cmd_dct = args[0]
        current_path = os.path.join(home, self.current)
        filename = os.path.join(current_path, cmd_dct["filename"])

        # 判断文件存在继续
        if os.path.isfile(filename):
            size = os.stat(filename).st_size
            msg_dct = {
                "isfile": True,  # 文件存在
                "filename": filename,
                "size": size,
            }

            # 第一次发送操作文件信息
            self.request.send(json.dumps(msg_dct).encode("utf-8"))
            server_response = self.request.recv(1024)  # 确认接收，防止粘包


            # 接着发送文件内容
            m = hashlib.md5()
            f = open(filename, "rb")
            for line in f:
                self.request.send(line)
                m.update(line)
            f.close()

            # 可以增加MD5校验
            self.request.send(m.hexdigest().encode("utf-8"))
            res = self.request.recv(1024).decode("utf-8")
            if res == "0":
                print("文件传输成功")
            else:
                print("文件传输失败")
        else:
            msg_dct = {
                "isfile": False,  # 文件不存在
                "filename": filename,
            }
            # 文件不存在文件信息
            self.request.send(json.dumps(msg_dct).encode("utf-8"))
            print("文件不存在 %s" % filename)

    def cd(self, *args):
        """服务器端，改变当前路径"""
        cmd_dct = args[0]
        dirname = cmd_dct["dirname"]
        current_path = os.path.join(home, self.current)
        if dirname == "..":
            # 每个用户的顶层目录为自己的用户名，不能再往上
            if self.current != self.username:
                self.current = os.path.dirname(current_path).replace(home, "")
        else:
            # 如果目录不存在则不能改变
            cd_path = os.path.join(current_path, dirname)
            if os.path.isdir(cd_path):
                self.current = cd_path.replace(home, "")

        # 返回操作结果
        msg_dct = {
            "current":self.current
        }
        self.request.send(json.dumps(msg_dct).encode("utf-8"))

    def ls(self, *args):
        """服务器端，查看当前路径下目录文件"""
        current_path = os.path.join(home, self.current)
        lst = os.listdir(current_path)
        msg_dct = {
            "list":lst
        }
        self.request.send(json.dumps(msg_dct).encode("utf-8"))

    def pwd(self, *args):
        """服务器端，查看当前路径"""
        msg_dct = {
            "current":self.current
        }
        self.request.send(json.dumps(msg_dct).encode("utf-8"))

    def mkdir(self, *args):
        """服务器端，创建目录"""
        cmd_dct = args[0]
        dirname = cmd_dct["dirname"]
        current_path = os.path.join(home, self.current)
        dir_path = os.path.join(current_path, dirname)
        os.mkdir(dir_path)
        self.current = dir_path.replace(home, "")
        msg_dct = {
            "current":self.current
        }
        self.request.send(json.dumps(msg_dct).encode("utf-8"))

def run():
    host, port = "localhost", 6969
    # server = socketserver.TCPServer((host, port), MyHandler)   # 单线程交互
    server = socketserver.ThreadingTCPServer((host, port), MyHandler)   # 多线程交互
    print("服务器已开启")
    server.serve_forever()


if __name__ == "__main__":
    run()