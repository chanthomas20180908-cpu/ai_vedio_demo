# OSS配置说明

## 配置步骤

### 1. 创建OSS配置文件

需要在My_files项目中创建OSS配置文件:

```bash
cd /Users/thomaschan/Code/My_files
cp env/default.env.example env/default.env
```

### 2. 填写配置信息

编辑 `/Users/thomaschan/Code/My_files/env/default.env`:

```env
ALIYUN_ACCESS_KEY=your_access_key_id
ALIYUN_ACCESS_SECRET=your_access_key_secret
ALIYUN_BUCKET_NAME=your_bucket_name
ALIYUN_BUCKET_ENDPORT=oss-cn-hangzhou.aliyuncs.com
```

**注意**: 这些是敏感信息,配置文件已在.gitignore中忽略,不会提交到git。

### 3. 验证配置

运行测试脚本验证OSS访问:

```bash
cd /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject
python3 utils/oss_file_accessor.py
```

### 4. 运行MVP测试

配置完成后即可运行MVP测试:

```bash
python3 debug/run_mvp_i2v_test.py
```

## 工作原理

### OSS访问流程

1. **文件路径转换**: 将旧的本地路径转换为OSS路径
   - 旧路径: `/Users/thomaschan/Code/My_files/my_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png`
   - OSS路径: `my_multimedia/my_images/slave/wan25_t2i_1765248811.png`

2. **URL获取与刷新**: 
   - 自动检查URL是否过期
   - 过期则重新生成签名URL(默认1小时有效期)
   - 缓存URL映射到本地记录文件

3. **文件下载**: 
   - 首次访问时从OSS下载到临时目录
   - 后续访问使用缓存文件(除非主动清除)
   - 临时目录: `/tmp/pythonProject_oss_cache/`

### URL过期管理机制

- **URL映射记录**: 存储在 `My_files/oss_records/url_mappings.json`
- **过期时间**: 每个URL都记录了过期时间
- **自动刷新**: 访问时自动检查并刷新过期URL
- **默认有效期**: 1小时(3600秒)

### 缓存管理

查看缓存目录:
```bash
ls -lh /tmp/pythonProject_oss_cache/
```

清除缓存:
```python
from utils.oss_file_accessor import get_oss_accessor

accessor = get_oss_accessor()
accessor.clear_cache()
```

## 使用示例

### 基础用法

```python
from utils.oss_file_accessor import download_oss_file, get_oss_url

# 方式1: 获取OSS文件URL
oss_path = "my_multimedia/my_images/test.png"
url = get_oss_url(oss_path)
print(f"访问URL: {url}")

# 方式2: 下载到本地临时目录
local_path = download_oss_file(oss_path)
print(f"本地路径: {local_path}")
```

### 高级用法

```python
from utils.oss_file_accessor import OSSFileAccessor

accessor = OSSFileAccessor()

# 获取URL(自定义过期时间)
url = accessor.get_file_url(
    oss_path="my_multimedia/my_images/test.png",
    auto_refresh=True,
    expire_seconds=7200  # 2小时
)

# 下载文件(不使用缓存)
local_path = accessor.download_to_temp(
    oss_path="my_multimedia/my_images/test.png",
    use_cache=False
)

# 检查文件是否存在
if accessor.file_exists("my_multimedia/my_images/test.png"):
    print("文件存在")

# 获取文件信息
info = accessor.get_file_info("my_multimedia/my_images/test.png")
print(f"文件大小: {info['size']} bytes")
```

## 故障排查

### 问题1: ModuleNotFoundError: No module named 'oss2'

```bash
pip3 install oss2 python-dotenv requests
```

### 问题2: ValueError: 缺少必要的环境变量

检查配置文件是否存在并正确填写:
```bash
cat /Users/thomaschan/Code/My_files/env/default.env
```

### 问题3: 文件不存在于OSS

确认文件已上传到OSS:
```bash
cd /Users/thomaschan/Code/My_files
python3 oss_manager.py list --path my_multimedia/my_images/
```

### 问题4: URL过期无法访问

重新生成URL:
```python
from utils.oss_file_accessor import get_oss_accessor

accessor = get_oss_accessor()
url = accessor.get_file_url("文件路径", auto_refresh=True)
```

## 优势

✅ **无需本地存储大文件** - 所有文件都在OSS上,本地只保存临时缓存
✅ **自动URL刷新** - 过期URL自动重新生成,无需手动管理
✅ **智能缓存** - 已下载的文件会缓存,避免重复下载
✅ **统一访问入口** - 所有OSS访问都通过统一接口,便于维护
✅ **透明切换** - debug脚本只需改一行代码即可从本地路径切换到OSS

## 相关文件

- OSS访问器: `pythonProject/utils/oss_file_accessor.py`
- OSS配置: `pythonProject/config/oss_config.py`
- OSS管理器: `My_files/oss_manager.py`
- 配置文件: `My_files/env/default.env`
- URL映射: `My_files/oss_records/url_mappings.json`
