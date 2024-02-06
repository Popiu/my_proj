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

