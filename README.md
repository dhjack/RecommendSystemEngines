# 推荐系统 -- 引擎部分
目前实现了三种推荐引擎：
1. 贝叶斯
2. ALS
3. LSI

## 加载数据

先确保数据库都是utf8的配置
```
#各种字符参数统一为utf8后，再使用 load data。
mysql> set character_set_database=utf8;
Query OK, 0 rows affected, 1 warning (0.00 sec)

mysql> set character_set_server=utf8;
Query OK, 0 rows affected (0.00 sec)

mysql> show variables like "%char%";
+--------------------------------------+----------------------------+
| Variable_name                        | Value                      |
+--------------------------------------+----------------------------+
| character_set_client                 | utf8                       |
| character_set_connection             | utf8                       |
| character_set_database               | utf8                       |
| character_set_filesystem             | binary                     |
| character_set_results                | utf8                       |
| character_set_server                 | utf8                       |
| character_set_system                 | utf8                       |
| character_sets_dir                   | /usr/share/mysql/charsets/ |
| validate_password_special_char_count | 1                          |
+--------------------------------------+----------------------------+
```
加载评分数据和电影信息到数据库
```
create database reSystem;

use reSystem;

CREATE TABLE `moviesJsonInfo` (
  `pid` int(10) unsigned NOT NULL,
  `info` mediumtext,
  PRIMARY KEY (`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `userRates` (
  `uid` varchar(64) NOT NULL,
  `pid` int(10) unsigned NOT NULL,
  `rate` int(10) unsigned NOT NULL,
  UNIQUE KEY `uid` (`uid`,`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 数据在data目录下，这里需要改为实际路径
LOAD DATA LOCAL INFILE '/tmp/t.movies.text' INTO TABLE moviesJsonInfo;
LOAD DATA LOCAL INFILE '/tmp/t.rating.text' INTO TABLE userRates;
```
## 安装依赖
```
pip install -r requirements.txt
```

## daemon模式运行
```
nohup python __init__.py
```

