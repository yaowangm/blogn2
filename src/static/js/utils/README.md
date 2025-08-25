# 注册码格式化工具

## 概述

`regkey-formatter.js` 是一个通用的注册码格式化工具，提供注册码的格式化、清理、验证等功能。

## 功能特性

### 1. 格式化注册码
将连续的注册码字符串格式化为每5个字符后添加"-"分隔符的格式。

**示例：**
```javascript
// 输入：E123B4354D01807B0D5B7EF45
// 输出：E123B-4354D-01807-B0D5B-7EF45
```

### 2. 清理注册码
移除注册码中的所有分隔符，返回纯字符串格式。

**示例：**
```javascript
// 输入：E123B-4354D-01807-B0D5B-7EF45
// 输出：E123B4354D01807B0D5B7EF45
```

### 3. 验证注册码格式
检查注册码是否符合标准格式（只包含字母和数字，长度合理）。

### 4. 获取显示长度
计算格式化后注册码的显示长度（包含分隔符）。

## 使用方法

### 方式1：ES6模块导入
```javascript
import { formatRegKey, cleanRegKey, validateRegKeyFormat } from '/static/js/utils/regkey-formatter.js';

// 格式化注册码
const formatted = formatRegKey('E123B4354D01807B0D5B7EF45');
console.log(formatted); // E123B-4354D-01807-B0D5B-7EF45

// 清理注册码
const cleaned = cleanRegKey('E123B-4354D-01807-B0D5B-7EF45');
console.log(cleaned); // E123B4354D01807B0D5B7EF45

// 验证格式
const isValid = validateRegKeyFormat('E123B-4354D-01807-B0D5B-7EF45');
console.log(isValid); // true
```

### 方式2：全局对象访问
```javascript
// 确保已加载 regkey-formatter.js
const formatted = window.RegKeyFormatter.format('E123B4354D01807B0D5B7EF45');
const cleaned = window.RegKeyFormatter.clean('E123B-4354D-01807-B0D5B-7EF45');
const isValid = window.RegKeyFormatter.validate('E123B-4354D-01807-B0D5B-7EF45');
```

## API 参考

### `formatRegKey(regkey)`
- **参数：** `regkey` (string) - 原始注册码字符串
- **返回：** (string) - 格式化后的注册码
- **描述：** 每5个字符后添加"-"分隔符

### `cleanRegKey(formattedRegkey)`
- **参数：** `formattedRegkey` (string) - 格式化后的注册码
- **返回：** (string) - 纯字符串格式的注册码
- **描述：** 移除所有分隔符

### `validateRegKeyFormat(regkey)`
- **参数：** `regkey` (string) - 注册码字符串
- **返回：** (boolean) - 格式是否正确
- **描述：** 验证注册码格式

### `getRegKeyDisplayLength(regkey)`
- **参数：** `regkey` (string) - 注册码字符串
- **返回：** (number) - 显示长度（包含分隔符）
- **描述：** 计算格式化后的显示长度

## 使用场景

1. **注册码管理页面** - 显示格式化的注册码
2. **用户注册流程** - 验证注册码格式
3. **API响应处理** - 格式化返回的注册码
4. **数据导入导出** - 清理和格式化注册码数据

## 注意事项

- 工具会自动处理已包含分隔符的注册码
- 支持不同长度的注册码（16-32位）
- 不区分大小写
- 兼容ES6模块和传统脚本加载方式
