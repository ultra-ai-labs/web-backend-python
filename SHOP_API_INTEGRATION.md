# 商城对接接口说明

本文档说明商城与 `web-backend-python` 后端的最小对接方式。

当前方案目标：

- 不依赖商城用户 ID
- 商城只需要传订单号、用户名、额度等基础信息
- 后端复用现有用户管理方式
- 手机号可直接作为系统 `username`
- 新用户自动开户并充值
- 老用户直接充值
- 所有商城订单都会落库记录，避免重复处理


## 鉴权方式

商城请求必须带请求头：

```http
x-shop-api: <约定的密钥>
Content-Type: application/json
```

后端会读取环境变量：

```text
SHOP_API_KEY
```

当 `x-shop-api` 与 `SHOP_API_KEY` 不一致时，接口返回：

```json
{
  "status": 401,
  "msg": "shop api unauthorized"
}
```


## 用户规则

- 后端系统自己的主键仍为 `user_id`
- 商城不需要传商城用户 ID
- 商城应直接传 `username`
- 推荐直接把手机号作为 `username`
- 若同时传了 `phone`，则仅作为兼容字段使用
- 新用户初始密码规则为：`username(手机号) + ultra-ai`

示例：

- 手机号：`18888888888`
- 初始密码：`18888888888ultra-ai`


## 订单处理规则

- 每个商城订单号 `order_no` 只能处理一次
- 同一个 `order_no` 重复调用会直接返回重复处理错误
- 所有订单都会记录到 `shop_order` 表


## 接口 1：查询用户是否存在

用于商城侧按手机号或用户名确认系统内用户是否已存在。

### 请求方式

```http
GET /shop/user/query
```

### 请求参数

使用 query 参数，二选一即可：

- `username`
- `phone`

优先级：

- 如果传了 `username`，优先按 `username` 查询
- 否则按 `phone` 查询

### 请求示例

```http
GET /shop/user/query?phone=18888888888
x-shop-api: your_shop_api_key
```

### 成功返回：用户存在

```json
{
  "status": 200,
  "msg": "success",
  "data": {
    "exists": true,
    "user_id": "1913123123123123",
    "username": "18888888888"
  }
}
```

### 成功返回：用户不存在

```json
{
  "status": 200,
  "msg": "user not found",
  "data": {
    "exists": false,
    "username": "18888888888"
  }
}
```

### 参数错误

```json
{
  "status": 400,
  "msg": "username or phone is required"
}
```


## 接口 2：订单充值接口

商城支付成功后，调用该接口给用户开户或充值。
商城侧不能直接传额度，必须传标准 `sku_type`，由后端内部映射为额度。

### 请求方式

```http
POST /shop/order/recharge
```

### 请求体

```json
{
  "order_no": "SHOP202604170001",
  "sku_type": 3,
  "amount": 199.00,
  "is_new_user": true,
  "username": "18888888888"
}
```

### 字段说明

- `order_no`
  - 商城订单号
  - 必填
  - 必须唯一

- `sku_type`
  - 商品类型
  - 必填
  - 只能传以下值：
    - `1`：10000 额度
    - `2`：50000 额度
    - `3`：100000 额度
  - 其他值一律视为无效

- `amount`
  - 可选
  - 订单金额
  - 仅用于记录订单信息
  - 不参与额度计算
  - 可为空，便于内部调用或 admin 使用

- `is_new_user`
  - 是否新用户
  - 必填
  - `true` 表示商城侧认为这是新开户
  - `false` 表示商城侧认为是已有账号充值

- `username`
  - 必填
  - 建议直接传手机号
  - 后端按该值查找或创建系统用户

- `phone`
  - 可选
  - 兼容字段
  - 如果不传，则默认使用 `username` 参与初始密码生成


## 订单接口处理逻辑

### 1. `is_new_user = true`

- 若系统中不存在该 `username`
  - 自动创建用户
  - 自动生成初始密码：`phone + ultra-ai`
  - 按 `sku_type` 对应额度自动增加额度
  - 记录商城订单
  - 返回 `create user and recharge success`

- 若系统中已存在该 `username`
  - 不再重复创建
  - 直接给该用户充值
  - 记录商城订单
  - 返回 `recharge success`

### 2. `is_new_user = false`

- 若系统中存在该 `username`
  - 直接充值
  - 记录商城订单
  - 返回 `recharge success`

- 若系统中不存在该 `username`
  - 返回用户不存在错误


## 成功返回示例

### 新建账号并充值成功

```json
{
  "status": 200,
  "msg": "create user and recharge success",
  "data": {
    "username": "18888888888"
  }
}
```

### 已有账号充值成功

```json
{
  "status": 200,
  "msg": "recharge success",
  "data": {
    "username": "18888888888"
  }
}
```


## 失败返回示例

### 订单重复

```json
{
  "status": 409,
  "msg": "order already processed"
}
```

### 老用户充值但用户不存在

```json
{
  "status": 404,
  "msg": "user not found"
}
```

### 参数缺失

```json
{
  "status": 400,
  "msg": "order_no, sku_type and username are required"
}
```

### sku_type 无效

```json
{
  "status": 400,
  "msg": "invalid sku_type"
}
```

### amount 无效

```json
{
  "status": 400,
  "msg": "invalid amount"
}
```

### 鉴权失败

```json
{
  "status": 401,
  "msg": "shop api unauthorized"
}
```


## 落库记录

商城订单会写入表：

```text
shop_order
```

主要字段：

- `order_no`
- `phone`
- `username`
- `user_id`
- `amount`
- `quota`
- `is_new_user`
- `status`
- `remark`
- `raw_payload`
- `create_time`
- `update_time`


## 接入建议

商城侧推荐调用顺序：

1. 可选：先调用 `/shop/user/query` 查询用户是否存在
2. 支付成功后调用 `/shop/order/recharge`
3. 根据返回的 `status / msg / data.username` 判断处理结果

如果商城侧不想调两次接口，也可以直接只调充值接口，由后端自行处理开户或充值逻辑。
