import os
import json

# 用户管理模块

# 用户信息文件存放路劲
users_path = r"..\users"

def add_user(name, password, total_size):
    """增加用户"""
    filename = os.path.join(users_path, name+".json")

    f = open(filename, "w")
    info = {
        "name":name,
        "password":password,
        "total_size":int(total_size),
        "used_size":0
    }
    json.dump(info, f, indent="\t")
    f.close()

def getinfo(name):
    """获取用户信息"""
    filename = os.path.join(users_path, name + ".json")

    f = open(filename, "r")
    info = json.load(f)
    f.close()
    return info

def add_used_size(name, size):
    """增加用户已用空间大小"""
    filename = os.path.join(users_path, name + ".json")

    f = open(filename, "r")
    info = json.load(f)
    f.close()

    f = open(filename, "w")
    info["used_size"] += int(size)
    json.dump(info, f, indent="\t")
    f.close()

    return info

def create_user(num):
    """自动初始化用户数据"""
    for i in range(1,num):
        name = str(i).zfill(3)
        password="1"
        total_size = 1000
        add_user(name, password, total_size)
    print("ok")

def run():
    name = input("name:")
    # # password = input("password:")
    # # total_size = input("total_size(bytes):")
    # # add_user(name, password, total_size)
    size = input("size:")
    add_used_size(name, size)

if __name__ == "__main__":
    # run()
    create_user(6)