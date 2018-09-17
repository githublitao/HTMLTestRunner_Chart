# HTMLTestRunner_Chart 基于unittest的测试报告，使用详情见demo
参考链接：
http://tungwaiyip.info/software/HTMLTestRunner.html<br>
https://github.com/GoverSky/HTMLTestRunner_cn<br>
# 优化报告内容
1. 测试报告中文显示，优化一些断言失败正文乱码问题<br>
2. 新增错误和失败截图，展示到html报告里<br>
3. 增加饼图统计<br>
4. 失败后重试功能<br>
5. 保存近10次测试结果，并通过柱状图展示<br>
6. 切换测试日期，展示历史测试结果<br>
兼容python2.x 和3.x
# 注意：
1. 在是python3.x 中，如果在这里setUp里初始化driver ，因为3.x版本 unittest 运行机制不同，会导致用力失败时截图失败，目前只有采用捕获异常来截图，或者在setUpClass里初始化driver<br>
2. 初始化必须命名为driver
# 报告首页：
![报告截图](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E9%A6%96%E9%A1%B5.png)<br>
# 用例截图：
![用例截图](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E6%98%BE%E7%A4%BA%E6%88%AA%E5%9B%BE.png)<br>
# 失败饼图：
![失败饼图](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E9%A5%BC%E5%9B%BE.png)<br>
# 历史走势：
![历史走势](https://github.com/githublitao/HTMLTestRunner_Chart/blob/master/img/%E8%B5%B0%E5%8A%BF%E5%9B%BE.png)<br>
# 微信打赏：
![微信打赏](https://github.com/githublitao/api_automation_test/blob/master/img/%E6%94%B6%E6%AC%BE%E7%A0%81.png)<br>
<br>
# 失败重试：
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
