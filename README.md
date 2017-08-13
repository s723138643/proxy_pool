
IP代理池
=======

> 基于aiohttp的代理池 

### 1、安装

下载代码:
```
git clone git@github.com:s723138643/proxy_pool.git

或者直接到https://github.com/s723138643/proxy_pool 下载zip文件
```

### 2、运行:

```
到克隆的目录下默认为proxy_pool:
>>>python main.py
```

　　任务启动后，自动载入proxy_getter目录中的插件，并通过插件实例的get_proxy方法获取代理, 此后默认每20分钟会重复执行一次。

### 3、使用

    获取代理：
    >> curl http://127.0.0.1:5000/get

爬虫中使用，如果要在爬虫代码中使用的话， 可以将此api封装成函数直接使用，例如:
```
import requests

def get_proxy():
    return requests.get("http://127.0.0.1:5000/get/").content
```

### 4、扩展

新建一个.py文件，编写Getter类通过get_proxy方法返回代理列表，最后将该文件放入proxy_getter目录即可

### 5、设置

可在settings.py中更改默认设置

### 6、许可

Apache License