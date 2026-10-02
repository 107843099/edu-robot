---
title: 2. 小智工程编译与下载
order: 2
---
本章内容介绍了使用VS Code，命令行的编译与下载方法以及sftool_GUI工具的下载方法
## VS Code 插件编译与下载小智工程

### 一、打开小智工程

首先，切换到前面拉取的小智工程所在的目录，并使用 VS Code 打开工程。

![打开小智工程](./assets/xiaozhi_sifli_sdk_codekit_openfile.png)

### 二、烧录与下载工程

1. 配置插件：

   - SDK版本选择前面配置的SDK。
   - 选择开发板型号为 `sf32lb52-xty-ai`。
   - 设置编译线程数为 `8`。
   - 选择串口号，波特率设置为 `1000000`。

2. 点击“构建”按钮，开始编译小智工程。

![配置 SDK](./assets/xiaozhi_sifli_sdk_codekit_setSDK.png)

3. 等待编译完成后，即可将工程烧录到开发板。

![烧录工程](./assets/xiaozhi_sifli_sdk_codekit_load.png)

4. 烧录成功后，开发板将自动重启并运行程序，效果如下图所示：

![运行效果](./assets/xiaozhi_command_result.png)

## 使用命令行编译与下载小智工程
### 一、编译小智工程

#### 1. 环境准备

1. **打开 PowerShell** 终端
2. **定位到 SDK 路径**：在小智工程中找到 SDK 目录，执行以下命令激活编译环境：

   ```bash
   .\export.ps1
   ```

#### 2. 执行编译

1. **切换工作目录**：进入小智工程的 `app/project` 文件夹，复制其路径
2. **在 PowerShell 中切换目录**：使用 `cd` 命令进入刚才复制的路径
3. **执行编译命令**：运行以下命令开始编译：

   ```bash
   scons --board=sf32lb52-xty-ai --board_search_path="..\boards" -j16
   ```

   **参数说明**：
   - `--board=sf32lb52-xty-ai`：指定目标开发板
   - `--board_search_path="..\boards"`：指定开发板配置文件搜索路径
   - `-j16`：使用 16 个线程并行编译，加快编译速度

#### 3. 编译完成确认

- 编译过程**耗时较长**，系统会对图片、动图等资源进行处理，请耐心等待
- 当看到以下输出时，表示编译成功：
  ```
  scons: done building targets
  ```
  
![编译成功提示](./assets/xiaozhi_command_loadprojcet.png)

### 二、下载工程到开发板

#### 1. 确认端口号

1. 打开 **设备管理器**
2. 在 **端口 (COM 和 LPT)** 下查看开发板对应的端口号（如 COM3、COM4）

#### 2. 执行下载

1. 在 PowerShell 终端中输入下载命令：
   ```bash
   build_sf32lb52-xty-ai_hcpu\uart_download.bat
   ```
2. 根据提示输入开发板的**端口号**
3. 等待下载进度完成

#### 3. 验证下载结果

1. 下载完成后，终端会显示成功提示
   ![下载成功提示](./assets/xiaozhi_command_uartload.png)
2. 开发板将自动重启并运行程序，效果如下：
   ![实际运行效果](./assets/xiaozhi_command_result.png)


## 使用Github Actions自动构建固件

Github Actions是GitHub提供的持续集成和持续部署（CI/CD）服务，可以帮助你自动化构建、测试和部署代码。通过配置工作流文件，你可以在每次代码推送或拉取请求时自动触发构建过程，从而确保代码始终处于可用状态。

具体内容参考：[小智百科全书源码构建-使用 GitHub Action 自动编译（可选）](https://docs.sifli.com/projects/xiaozhi/source-build/)

## 使用其他方法下载（烧录）固件

具体内容参考：
[使用ui界面烧录固件](https://docs.sifli.com/projects/xiaozhi/get-started/sftool_gui)
[使用终端命令烧录固件](https://docs.sifli.com/projects/xiaozhi/get-started/sftool_cmd)
