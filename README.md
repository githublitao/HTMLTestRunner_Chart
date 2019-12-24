# HTMLTestRunner_Chart 基于unittest的测试报告，使用详情见demo
参考链接：<br>
http://tungwaiyip.info/software/HTMLTestRunner.html<br>
https://github.com/GoverSky/HTMLTestRunner_cn<br>
### 优化报告内容
1. 测试报告中文显示，优化一些断言失败正文乱码问题<br>
2. 新增错误和失败截图，展示到html报告里<br>
3. 增加饼图统计<br>
4. 失败后重试功能<br>
5. 保存近10次测试结果，并通过柱状图展示<br>
6. 切换测试日期，展示历史测试结果<br>
兼容python2.x 和3.x
### 注意：
1. 在是python3.x 中，如果在这里setUp里初始化driver ，因为3.x版本 unittest 运行机制不同，会导致用力失败时截图失败，目前只有采用捕获异常来截图，或者在setUpClass里初始化driver<br>
2. driver初始化变量名必须命名为driver
### 报告首页：
![报告截图](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E9%A6%96%E9%A1%B51.png)<br>
### 用例截图：
![用例截图](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E6%98%BE%E7%A4%BA%E6%88%AA%E5%9B%BE1.png)<br>
### 失败饼图：
![失败饼图](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E9%A5%BC%E5%9B%BE1.png)<br>
### 历史走势：
![历史走势](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E8%B5%B0%E5%8A%BF%E5%9B%BE1.png)<br>
### 微信打赏：
![微信打赏](https://github.com/githublitao/api_automation_test/blob/master/img/%E6%94%B6%E6%AC%BE%E7%A0%811.png)<br>
<br>
### 失败重试：
1. 生成报告的参数里面加了一个参数retry=1,这个表示用例失败后，会重新跑一次。<br>
```python
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(case_01)
    runner = HTMLTestRunner(
        title="带截图，饼图，折线图，历史结果查看的测试报告",
        description="",
        stream=open("./demo.html", "wb"),
        verbosity=2,
        retry=0,
        save_last_try=True)
    runner.run(suite)
```
### 保存测试结果到json文件：
```python
    def mkdir_json(self):
        is_exists = os.path.exists(self.path)
        # 判断结果
        if not is_exists:
            try:
                # 如果不存在则创建目录
                # 创建目录操作函数
                with open(self.path, "w+") as f:
                    f.write("var data = []")
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return True

    def Write(self, title, heading, desc, data):
        try:
            with open(self.path, "r+") as f:
                all_data = f.read().split(" = ", 1)
                data_json = all_data[1]
                data_json = eval(data_json)
                if len(data_json) >= 10:
                    del data_json[0]
                description = dict()
                description["startTime"] = heading[0][1]
                description["duration"] = heading[1][1]
                if PY3K:
                    description["title"] = title
                    description["status"] = heading[2][1]
                    description["desc"] = desc
                    description["data"] = data
                    status = heading[2][1].split(" ")
                    for j in range(0, len(status)):
                        if status[j] == "通过":
                            description["success"] = str(status[j + 1])
                        if status[j] == "失败":
                            description["fail"] = str(status[j + 1])
                        if status[j] == "错误":
                            description["error"] = str(status[j + 1])
                else:
                    description["title"] = title.encode("gbk")
                    description["status"] = heading[2][1].encode("gbk")
                    description["desc"] = desc.encode("gbk")
                    description["data"] = data.encode("gbk")
                    status = heading[2][1].split(" ")
                    for j in range(0, len(status)):
                        if status[j] == u"通过":
                            description["success"] = str(status[j + 1])
                        if status[j] == u"失败":
                            description["fail"] = str(status[j + 1])
                        if status[j] == u"错误":
                            description["error"] = str(status[j + 1])
                data_json.append(description)
                data_json = str(data_json)
                f.seek(0)
                f.truncate()
                f.write(str("var data = " + data_json))
        except IndexError:
            sys.stderr.write("JSON初始化内容有误! 初始化内容’var data = []‘")
```
### 错误/失败截图，修改addError和addFail函数：
```python
    def addFailure(self, test, err):
        self.failure_count += 1
        self.status = 1
        TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str))
        if not getattr(test, "driver",""):
            pass
        else:
            try:
                driver = getattr(test, "driver")
                test.imgs.append(driver.get_screenshot_as_base64())
            except Exception as e:
                pass
        if self.verbosity > 1:
            sys.stderr.write('F  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('F')
```
### 错误重试，修改stopTest函数：
 ```python
     def stopTest(self, test):
        # Usually one of addSuccess, addError or addFailure would have been called.
        # But there are some path in unittest that would bypass this.
        # We must disconnect stdout in stopTest(), which is guaranteed to be called.
        if self.retry:
            if self.status == 1:
                self.trys += 1
                if self.trys <= self.retry:
                    if self.save_last_try:
                        t = self.result.pop(-1)
                        if t[0]==1:
                            self.failure_count-=1
                        else:
                            self.error_count -= 1
                    test=copy.copy(test)
                    sys.stderr.write("Retesting... ")
                    sys.stderr.write(str(test))
                    sys.stderr.write('..%d \n' % self.trys)
                    doc = test._testMethodDoc or ''
                    if doc.find('_retry')!=-1:
                        doc = doc[:doc.find('_retry')]
                    desc ="%s_retry:%d" %(doc, self.trys)
                    if not PY3K:
                        if isinstance(desc, str):
                            desc = desc.decode("utf-8")
                    test._testMethodDoc = desc
                    test(self)
                else:
                    self.status = 0
                    self.trys = 0
        self.complete_output()
 ```
### HTML模板导入JSON历史结果，如果JSON出现错误，则历史结果和走势图错误：
 ```html
 <head>
    <title>%(title)s</title>
    <meta name="generator" content="%(generator)s"/>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
    <script type="text/javascript" src="%(jsonpath)s" charset="gbk"></script>
    <link href="http://cdn.bootcss.com/bootstrap/3.3.0/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.bootcss.com/echarts/3.8.5/echarts.common.min.js"></script>
    <!-- <script type="text/javascript" src="js/echarts.common.min.js"></script> -->
    
    %(stylesheet)s
    
</head>
 ```
