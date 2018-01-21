# 作业：开发一个支持多用户在线的FTP程序

## 要求：

1. 用户加密认证
2. 允许同时多用户登录
3. 每个用户有自己的家目录 ，且只能访问自己的家目录
4. 对用户进行磁盘配额，每个用户的可用空间不同
5. 允许用户在ftp server上随意切换目录
6. 允许用户查看前目录下文件
7. 允许上传和下载文件，保证文件一致性
8. 文件传输过程中显示进度条（显示过多，已屏蔽）
9. 附加功能：支持文件的断点续传（暂时没实现）


## 用户数据结构
```
{
    "name":name,
    "password":password,
    "total_size":size,
    "used_size":size,
}
```

## 项目目录结构

### 客户端
```
ftp_client                    # 客户端
    bin
        main.py               # 程序执行入口
        1.png                 # 测试文件
    core
        client.py             # 客户端文件
    conf                      #配置文件，暂时为空
    log                       # 日志文件，暂时为空

```
### 服务器端
```
ftp_server                    # 服务器
    bin
        main.py               # 程序执行入口
    core
        server.py             # 服务器端文件
        user_manager.py       # 客户信息管理
    files
        001                   # 用户目录
            image             # 通过客户端新建的文件夹
            1.png             # 通过客户端上传的文件
    users
        001                   # 用户信息文件
        002
        003
        ...
    log                       # 日志文件夹，暂时没使用
```

##  程序启动入口
服务器端：ftp_server/bin/main.py

客户端：ftp_server/bin/main.py