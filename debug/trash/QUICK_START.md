# OSS集成快速开始

## 🚀 3步配置OSS访问

### 第1步: 创建配置文件 (30秒)
```bash
cd /Users/thomaschan/Code/My_files
cp env/default.env.example env/default.env
```

### 第2步: 填写配置 (1分钟)
编辑 `/Users/thomaschan/Code/My_files/env/default.env`:
```env
ALIYUN_ACCESS_KEY=你的AccessKey
ALIYUN_ACCESS_SECRET=你的AccessSecret  
ALIYUN_BUCKET_NAME=你的Bucket名称
ALIYUN_BUCKET_ENDPORT=oss-cn-hangzhou.aliyuncs.com
```

### 第3步: 验证配置 (30秒)
```bash
cd /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject
python3 debug/test_oss_integration.py
```

## ✅ 完成!

现在可以运行MVP测试了:
```bash
python3 debug/run_mvp_i2v_test.py
```

---

## 📖 详细文档

- **配置指南**: `OSS_SETUP.md`
- **实施总结**: `OSS_IMPLEMENTATION_SUMMARY.md`
- **MVP测试说明**: `MVP_README.md`

## 🆘 遇到问题?

### 问题1: 缺少依赖
```bash
pip3 install oss2 python-dotenv requests
```

### 问题2: 配置错误
检查配置文件:
```bash
cat /Users/thomaschan/Code/My_files/env/default.env
```

### 问题3: 文件不存在
确认文件在OSS上:
```bash
cd /Users/thomaschan/Code/My_files
python3 oss_manager.py list --path my_multimedia/my_images/
```

## 💡 核心改动

**只改了一行代码**:
```python
# 旧: 本地路径
i_path_test = "/Users/thomaschan/Code/My_files/my_files/my_multimedia/my_images/slave/wan25_t2i_1765248811.png"

# 新: OSS路径 + 自动下载
oss_image_path = "my_multimedia/my_images/slave/wan25_t2i_1765248811.png"
i_path_test = download_oss_file(oss_image_path)
```

**自动实现**:
- ✅ URL过期自动刷新(默认1小时)
- ✅ 文件智能缓存(避免重复下载)
- ✅ 透明本地访问(其他代码无需改动)

---

**就是这么简单! 🎉**
