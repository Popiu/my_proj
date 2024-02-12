# 帧结构说明
## Regular帧格式
| 字段     | 缩写        | 长度    | 说明                      |
| -------- | ----------- | ------- | ------------------------- |
| Type     | msg_type    | 1       | 帧类型 (1)                |
| Sender   | sender_addr | 1       | 发送者地址                |
| Receiver | recv_addr   | 1       | 接收者地址，255为广播地址 |
| Message  | msg         | Unknown | 发送内容                  |

## RREQ帧格式
| 字段        | 缩写        | 长度 | 说明                      |
| ----------- | ----------- | ---- | ------------------------- |
| Type        | msg_type    | 1    | 帧类型 (1)                |
| Sender      | sender_addr | 1    | 发送者地址                |
| Receiver    | recv_addr   | 1    | 接收者地址，255为广播地址 |
| RREQ_ID     | rreq_id     | 1    | RREQ的序列号              |
| RREQ_SRC    | src_addr    | 1    | RREQ源地址                |
| SRC_SEQ_NUM | src_seq     | 1    | RREQ源序列号              |
| RREQ_DST    | dst_addr    | 1    | RREQ目的地址              |
| DST_SEQ_NUM | dst_seq     | 1    | RREQ目的序列号            |
| Hop_Count   | hop_cnt     | 1    | 跳数                      |

## RREP帧格式
| 字段      | 缩写        | 长度 | 说明                           |
| --------- | ----------- | ---- | ------------------------------ |
| Type      | msg_type    | 2    | 帧类型 (2)                     |
| Sender    | sender_addr | 1    | 发送者地址                     |
| Receiver  | recv_addr   | 1    | 接收者地址，255为广播地址      |
| RREP_DST  | dst_addr    | 1    | RREP目的地址，为RREQ询问的地址 |
| DST_SEQ   | dst_seq     | 1    | RREP目的序列号                 |
| RREP_SRC  | src_addr    | 1    | RREP源地址，为发出RREQ的地址   |
| Hop_Count | hop_cnt     | 1    | 跳数                           |

# 实验操作说明
## 定期路由信息刷新与错误报告
- 启动`main.py`
- 等待一段时间，节点之间互相发送HELLO报文，建立邻居关系（发送间隔为10秒）
- 输入`show 1`，检查节点1的路由表，应该获取到了节点0和节点2的路由信息
- 输入`down 2`，关闭节点2（移动到很远的地方）
- 输入`show 1`，检查节点1的路由表，应该发现节点2的路由信息变为inactive（大概30秒，路由信息会过期）

## AODV协议综合测试
- 启动`main.py`，记得将测试设置改为`test_config_0.json`
- 等待一段时间，节点之间互相发送HELLO报文，建立邻居关系（发送间隔为10秒）
- 输入`show 0`，检查节点0的路由表，此时只有通往邻居的路由信息
- 输入`send 0 2 test_msg`，节点0向节点2发送数据包test_msg
- 输入`show 0`，检查节点0的路由表，此时节点0应该获取到了节点2的路由信息
- 输入`down 1`，关闭节点1，此时所有节点1的邻居发出RERR报文，通知其他节点节点1不可达。并发出RREQ报文，寻找新的路由
- 输入`show 0`，检查节点0的路由表（等待30秒，等hello信息超时，路由表才会变化）
- 输入`send 0 2 test_msg2`，节点0向节点2发送数据包test_msg2
- 输入`show 0`，检查节点0的路由表