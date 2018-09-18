# -*- coding: utf-8 -*-
"""
A TestRunner for use with the Python unit testing framework. It
generates a HTML report to show the result at a glance.

The simplest way to use this is to invoke its main method. E.g.

    import unittest
    import HTMLTestRunner

    ... define your tests ...

    if __name__ == '__main__':
        HTMLTestRunner.main()


For more customization options, instantiates a HTMLTestRunner object.
HTMLTestRunner is a counterpart to unittest's TextTestRunner. E.g.

    # output to a file
    fp = file('my_report.html', 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
                stream=fp,
                title='My unit test',
                description='This demonstrates the report output by HTMLTestRunner.'
                )

    # Use an external stylesheet.
    # See the Template_mixin class for more customizable options
    runner.STYLESHEET_TMPL = '<link rel="stylesheet" href="my_stylesheet.css" type="text/css">'

    # run the test
    runner.run(my_test_suite)


------------------------------------------------------------------------
Copyright (c) 2004-2007, Wai Yip Tung
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name Wai Yip Tung nor the names of its contributors may be
  used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# URL: http://tungwaiyip.info/software/HTMLTestRunner.html
import os

__author__ = "Wai Yip Tung"
__version__ = "0.9.1"

"""
Change History
Version 0.9.1
* 用Echarts添加执行情况统计图 (灰蓝)

Version 0.9.0
* 改成Python 3.x (灰蓝)

Version 0.8.3
* 使用 Bootstrap稍加美化 (灰蓝)
* 改为中文 (灰蓝)

Version 0.8.2
* Show output inline instead of popup window (Viorel Lupu).

Version in 0.8.1
* Validated XHTML (Wolfgang Borgert).
* Added description of test classes and test cases.

Version in 0.8.0
* Define Template_mixin class for customization.
* Workaround a IE 6 bug that it does not treat <script> block as CDATA.

Version in 0.7.1
* Back port to Python 2.3 (Frank Horowitz).
* Fix missing scroll bars in detail log (Podi).
"""

# TODO: color stderr
# TODO: simplify javascript using ,ore than 1 class in the class attribute?

import datetime
import sys
import unittest
from xml.sax import saxutils

PY3K = (sys.version_info[0] > 2)
if PY3K:
    import io as StringIO
else:
    import StringIO
import copy

# ------------------------------------------------------------------------
# The redirectors below are used to capture output during testing. Output
# sent to sys.stdout and sys.stderr are automatically captured. However
# in some cases sys.stdout is already cached before HTMLTestRunner is
# invoked (e.g. calling logging.basicConfig). In order to capture those
# output, use the redirectors for the cached stream.
#
# e.g.
#   >>> logging.basicConfig(stream=HTMLTestRunner.stdout_redirector)
#   >>>


class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()


stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


# ----------------------------------------------------------------------
# Template


class Template_mixin(object):
    """
    Define a HTML template for report customerization and generation.

    Overall structure of an HTML report

    HTML
    +------------------------+
    |<html>                  |
    |  <head>                |
    |                        |
    |   STYLESHEET           |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </head>               |
    |                        |
    |  <body>                |
    |                        |
    |   HEADING              |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   REPORT               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   ENDING               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </body>               |
    |</html>                 |
    +------------------------+
    """

    STATUS = {
        0: u'通过',
        1: u'失败',
        2: u'错误',
    }

    DEFAULT_TITLE = 'Unit Test Report'
    DEFAULT_DESCRIPTION = ''

    # ------------------------------------------------------------------------
    # HTML Template

    HTML_TMPL = r"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
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
<body>
    <script language="javascript" type="text/javascript"><!--
    output_list = Array();

    /* level - 0:Summary; 1:Failed; 2:All */
    console.log(data)
    function showCase(level) {
        trs = document.getElementsByTagName("tr");
        for (var i = 2; i < trs.length; i++) {
            let tr = trs[i];
            var result = tr.getElementsByTagName("td")[0].className
            if (result === "passCase"){
                if (level === 2 || level === 3){
                    tr.className = '';
                } else {
                    tr.className = 'hiddenRow';
                }
            }
            if (result === "failCase"){
                if (level === 1 || level === 3){
                    tr.className = '';
                }else {
                    tr.className = 'hiddenRow';
                }
            }
            if (result === "errorCase"){
                if (level === 4 || level === 3){
                    tr.className = '';
                }else {
                    tr.className = 'hiddenRow';
                }
            }
        }

    }
    function showClassDetail(cid, count) {
        var id_list = Array(count);
        var toHide = 1;
        for (var i = 0; i < count; i++) {
            tid0 = 't' + cid.substr(1) + '.' + (i+1);
            tid = 'f' + tid0;
            tr = document.getElementById(tid);
            if (!tr) {
                tid = 'p' + tid0;
                tr = document.getElementById(tid);
            }
            id_list[i] = tid;
            if (tr.className) {
                toHide = 0;
            }
        }
        for (var i = 0; i < count; i++) {
            tid = id_list[i];
            if (toHide) {
                document.getElementById('div_'+tid).style.display = 'none';
                document.getElementById(tid).className = 'hiddenRow';
            }
            else {
                document.getElementById(tid).className = '';
            }
        }
    }


    function showTestDetail(div_id){
        var details_div = document.getElementById(div_id);
        var displayState = details_div.style.display;
        // alert(displayState)
        if (displayState !== 'block' ) {
            displayState = 'block'
            details_div.style.display = 'block'
        }
        else {
            details_div.style.display = 'none'
        }
    }


    function html_escape(s) {
        s = s.replace(/&/g,'&amp;');
        s = s.replace(/</g,'&lt;');
        s = s.replace(/>/g,'&gt;');
        return s;
    }
    
    
    function show_img(obj) {
        var obj1 = obj.nextElementSibling;
        obj1.style.display='block';
        var index = 0;//每张图片的下标，
        var len = obj1.getElementsByTagName('img').length;
        var imgyuan = obj1.getElementsByClassName('imgyuan')[0];
        //var start=setInterval(autoPlay,500);
        obj1.onmouseover=function(){//当鼠标光标停在图片上，则停止轮播
            clearInterval(start);
        }
        obj1.onmouseout=function(){//当鼠标光标停在图片上，则开始轮播
            start=setInterval(autoPlay,1000);
        }    
        for (var i = 0; i < len; i++) {
            var font = document.createElement('font');
            imgyuan.appendChild(font)
        }
        var lis = obj1.getElementsByTagName('font');//得到所有圆圈
        changeImg(0);
        var funny = function (i) {
            lis[i].onmouseover = function () {
                index=i;
                changeImg(i)
            }
        }
        for (var i = 0; i < lis.length; i++) {
            funny(i);
        }
        
        function autoPlay(){
            if(index>len-1){
                index=0;
                clearInterval(start); //运行一轮后停止
            }
            changeImg(index++);
        }
        imgyuan.style.width= 25*len +"px";
        //对应圆圈和图片同步
        function changeImg(index) {
            var list = obj1.getElementsByTagName('img');
            var list1 = obj1.getElementsByTagName('font');
            for (i = 0; i < list.length; i++) {
                list[i].style.display = 'none';
                list1[i].style.backgroundColor = 'white';
            }
            list[index].style.display = 'block';
            list1[index].style.backgroundColor = 'blue';
        }
    
    }
    function hide_img(obj){
        obj.parentElement.style.display = "none";
        obj.parentElement.getElementsByClassName('imgyuan')[0].innerHTML = "";
    }
    window.onload=function (){
        var objSelectet = document.getElementById("testTime");
        for(var i = data.length-1 ; i >=0 ; i--){
            var objOption = document.createElement("OPTION");
            objOption.text = data[i]["startTime"];
            objOption.value = i;
            objSelectet.options.add(objOption);
        }
        let successrate = [];
        let failrate = [];
        let errorrate = [];
        for (var j = 0 ; j < data.length; j++){
            if ( data[j]["success"] === undefined) {
                data[j]["success"] = 0
            }
            if ( data[j]["fail"] === undefined) {
                data[j]["fail"] = 0
            }
            if ( data[j]["error"] === undefined) {
                data[j]["error"] = 0
            }
            console.log(data[j]["success"], data[j]["fail"],data[j]["error"])
            let totle = Number(data[j]["success"])+Number(data[j]["fail"])+Number(data[j]["error"]);
            console.log(totle)
            successrate.push((Number(data[j]["success"])/totle)*100);
            failrate.push((Number(data[j]["fail"])/totle)*100);
            errorrate.push((Number(data[j]["error"])/totle)*100)
        }
        console.log(successrate, failrate, errorrate)
        let myChartline = echarts.init(document.getElementById('chartline'));
        // 绘制图表
        let optionline = {
            title: {
                text: '近十次测试结果',
                left: 'center',
                top: 20,
                textStyle: {
                    color: '#ccc'
                }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross',
                    crossStyle: {
                        color: '#999'
                    }
                }
            },
            toolbox: {
                feature: {
                    dataView: {show: true, readOnly: false},
                    magicType: {show: true, type: ['line', 'bar']},
                    restore: {show: true},
                    saveAsImage: {show: true}
                }
            },
            legend: {
                data:['通过率','失败率','错误率']
            },
            xAxis: [
                {
                    type: 'category',
                    data: ['1','2','3','4','5','6','7','8','9','10'],
                    axisPointer: {
                        type: 'shadow'
                    }
                }
            ],
            yAxis: [
                {
                    type: 'value',
                    name: '百分比',
                    min: 0,
                    max: 100,
                    interval: 20,
                    axisLabel: {
                        formatter: '{value} %%'
                    }
                },
            ],
            series: [
                {
                    name:'失败率',
                    type:'bar',
                    data:failrate
                    // data: [20, 10, 15, 2, 8, 56, 45, 10, 48, 1]
                },
                {
                    name:'错误率',
                    type:'line',
                    // yAxisIndex: 1,
                    data:errorrate
                    // data: [1, 5, 7, 2, 5, 6, 1, 0, 4, 7]
                },
                {
                    name:'通过率',
                    type:'bar',
                    data: successrate
                    // data: [79, 85, 78, 96, 87, 48, 54, 90, 52, 8]
                },
            ]
        };
        myChartline.setOption(optionline);
    }
    function changeResult(obj) {
        var objSelectet = document.getElementById("testTime");
        console.log(data[objSelectet.value])
        document.getElementById("title").innerText=data[objSelectet.value]["title"];
        document.getElementsByClassName("attribute")[0].innerHTML='<strong>开始时间：</strong>'+data[objSelectet.value]["startTime"];
        document.getElementsByClassName("attribute")[1].innerHTML='<strong>运行时长：</strong>'+data[objSelectet.value]["duration"];
        document.getElementsByClassName("attribute")[2].innerHTML='<strong>状态：</strong>'+data[objSelectet.value]["status"];
         document.getElementById("btn-group").innerHTML=data[objSelectet.value]["data"];
         this.changChart(data[objSelectet.value]["success"],data[objSelectet.value]["fail"],data[objSelectet.value]["error"])
    }
    function changChart(success, fail, error) {
        var myChart = echarts.init(document.getElementById('chart'));
        // 指定图表的配置项和数据
        var option = {
            title : {
                text: '测试执行情况',
                x:'center'
            },
            tooltip : {
                trigger: 'item',
                formatter: "{a} <br/>{b} : {c} ({d}%%)"
            },
            color: ['#95b75d', 'grey', '#b64645'],
            legend: {
                orient: 'vertical',
                left: 'left',
                data: ['通过','失败','错误']
            },
            series : [
                {
                    name: '测试执行情况',
                    type: 'pie',
                    radius : '60%%',
                    center: ['50%%', '60%%'],
                    data:[
                        {value:success, name:'通过'},
                        {value:fail, name:'失败'},
                        {value:error, name:'错误'}
                    ],
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
     }
    /* obsoleted by detail in <div>
    function showOutput(id, name) {
        var w = window.open("", //url
                        name,
                        "resizable,scrollbars,status,width=800,height=450");
        d = w.document;
        d.write("<pre>");
        d.write(html_escape(output_list[id]));
        d.write("\n");
        d.write("<a href='javascript:window.close()'>close</a>\n");
        d.write("</pre>\n");
        d.close();
    }
    */
    --></script>

    <div id="div_base">
        %(heading)s
        %(report)s
        %(ending)s
        %(chart_script)s
    </div>
</body>
</html>
"""  # variables: (title, generator, stylesheet, heading, report, ending, chart_script)

    ECHARTS_SCRIPT = """
    <script type="text/javascript">
        // 基于准备好的dom，初始化echarts实例
        var myChart = echarts.init(document.getElementById('chart'));

        // 指定图表的配置项和数据
        var option = {
            title : {
                text: '测试执行情况',
                x:'center'
            },
            tooltip : {
                trigger: 'item',
                formatter: "{a} <br/>{b} : {c} ({d}%%)"
            },
            color: ['#95b75d', 'grey', '#b64645'],
            legend: {
                orient: 'vertical',
                left: 'left',
                data: ['通过','失败','错误']
            },
            series : [
                {
                    name: '测试执行情况',
                    type: 'pie',
                    radius : '60%%',
                    center: ['50%%', '60%%'],
                    data:[
                        {value:%(Pass)s, name:'通过'},
                        {value:%(fail)s, name:'失败'},
                        {value:%(error)s, name:'错误'}
                    ],
                    itemStyle: {
                        emphasis: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };

        // 使用刚指定的配置项和数据显示图表。
        myChart.setOption(option);
    </script>
    """  # variables: (Pass, fail, error)

    # ------------------------------------------------------------------------
    # Stylesheet
    #
    # alternatively use a <link> for external style sheet, e.g.
    #   <link rel="stylesheet" href="$url" type="text/css">

    STYLESHEET_TMPL = """
<style type="text/css" media="screen">
    body        { font-family: Microsoft YaHei,Consolas,arial,sans-serif; font-size: 80%; }
    table       { font-size: 100%; }
    pre         { white-space: pre-wrap;word-wrap: break-word; }

    /* -- heading ---------------------------------------------------------------------- */
    h1 {
        font-size: 16pt;
        color: gray;
    }
    .heading {
        margin-top: 0ex;
        margin-bottom: 1ex;
    }

    .heading .attribute {
        margin-top: 1ex;
        margin-bottom: 0;
    }

    .heading .description {
        margin-top: 2ex;
        margin-bottom: 3ex;
    }

    /* -- css div popup ------------------------------------------------------------------------ */
    a.popup_link {
    }

    a.popup_link:hover {
        color: red;
    }
    .img{
        height: 100%;
        border-collapse: collapse;
        border: 2px solid #777;
    }
    .screenshots {
        z-index: 100;
        position:absolute;
        height: 80%;
        left: 50%;
        top: 50%;
        transform: translate(-50%,-50%);
        display: none;
    }
    .imgyuan{
        height: 20px;
        border-radius: 12px;
        background-color: red;
        padding-left: 13px;
        margin: 0 auto;
        position: relative;
        top: -40px;
        background-color: rgba(1, 150, 0, 0.3);
    }
    .imgyuan font{
        border:1px solid white;
        width:11px; 
        height:11px;
        border-radius:50%;
        margin-right: 9px;
        margin-top: 4px;
        display: block;
        float: left;
        background-color: white;
    }
    .close_shots {
        background-image: url(data:image/png;base64,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/GMzLdsAAD+3aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJBZG9iZSBYTVAgQ29yZSA1LjYtYzA2NyA3OS4xNTc3NDcsIDIwMTUvMDMvMzAtMjM6NDA6NDIgICAgICAgICI+CiAgIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAgICAgIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIgogICAgICAgICAgICB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIgogICAgICAgICAgICB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIKICAgICAgICAgICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICAgICAgICAgICB4bWxuczpwaG90b3Nob3A9Imh0dHA6Ly9ucy5hZG9iZS5jb20vcGhvdG9zaG9wLzEuMC8iCiAgICAgICAgICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgICAgICAgICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iCiAgICAgICAgICAgIHhtbG5zOmV4aWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vZXhpZi8xLjAvIj4KICAgICAgICAgPHhtcE1NOkRvY3VtZW50SUQ+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjk4NDVkYzlhLTM2NTEtMTFlOC1hMDRjLWMzZmRjNzFmNjFkZDwveG1wTU06RG9jdW1lbnRJRD4KICAgICAgICAgPHhtcE1NOkluc3RhbmNlSUQ+eG1wLmlpZDo3YzQ4OTMyZS0wM2FjLTIxNDctYTJiZi1iNmViOWU4ZDY2Y2Q8L3htcE1NOkluc3RhbmNlSUQ+CiAgICAgICAgIDx4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ+MEIzOTNDRjk1RDQ0RDlGMDNFQjEzQkZEQ0UxRDA5MjM8L3htcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD4KICAgICAgICAgPHhtcE1NOkhpc3Rvcnk+CiAgICAgICAgICAgIDxyZGY6U2VxPgogICAgICAgICAgICAgICA8cmRmOmxpIHJkZjpwYXJzZVR5cGU9IlJlc291cmNlIj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OmFjdGlvbj5zYXZlZDwvc3RFdnQ6YWN0aW9uPgogICAgICAgICAgICAgICAgICA8c3RFdnQ6aW5zdGFuY2VJRD54bXAuaWlkOmQ0ZjMzNDFjLTRkYjctZjc0YS1iZTAxLWYxMGEwMzNhNjg4ZDwvc3RFdnQ6aW5zdGFuY2VJRD4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OndoZW4+MjAxOC0wNC0wMlQxNjo0MToxMCswODowMDwvc3RFdnQ6d2hlbj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OnNvZnR3YXJlQWdlbnQ+QWRvYmUgUGhvdG9zaG9wIEVsZW1lbnRzIDE0LjAgKFdpbmRvd3MpPC9zdEV2dDpzb2Z0d2FyZUFnZW50PgogICAgICAgICAgICAgICAgICA8c3RFdnQ6Y2hhbmdlZD4vPC9zdEV2dDpjaGFuZ2VkPgogICAgICAgICAgICAgICA8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaSByZGY6cGFyc2VUeXBlPSJSZXNvdXJjZSI+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDphY3Rpb24+Y29udmVydGVkPC9zdEV2dDphY3Rpb24+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDpwYXJhbWV0ZXJzPmZyb20gaW1hZ2UvanBlZyB0byBpbWFnZS9wbmc8L3N0RXZ0OnBhcmFtZXRlcnM+CiAgICAgICAgICAgICAgIDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpIHJkZjpwYXJzZVR5cGU9IlJlc291cmNlIj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OmFjdGlvbj5kZXJpdmVkPC9zdEV2dDphY3Rpb24+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDpwYXJhbWV0ZXJzPmNvbnZlcnRlZCBmcm9tIGltYWdlL2pwZWcgdG8gaW1hZ2UvcG5nPC9zdEV2dDpwYXJhbWV0ZXJzPgogICAgICAgICAgICAgICA8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaSByZGY6cGFyc2VUeXBlPSJSZXNvdXJjZSI+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDphY3Rpb24+c2F2ZWQ8L3N0RXZ0OmFjdGlvbj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0Omluc3RhbmNlSUQ+eG1wLmlpZDo3YzQ4OTMyZS0wM2FjLTIxNDctYTJiZi1iNmViOWU4ZDY2Y2Q8L3N0RXZ0Omluc3RhbmNlSUQ+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDp3aGVuPjIwMTgtMDQtMDJUMTY6NDE6MTArMDg6MDA8L3N0RXZ0OndoZW4+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDpzb2Z0d2FyZUFnZW50PkFkb2JlIFBob3Rvc2hvcCBFbGVtZW50cyAxNC4wIChXaW5kb3dzKTwvc3RFdnQ6c29mdHdhcmVBZ2VudD4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OmNoYW5nZWQ+Lzwvc3RFdnQ6Y2hhbmdlZD4KICAgICAgICAgICAgICAgPC9yZGY6bGk+CiAgICAgICAgICAgIDwvcmRmOlNlcT4KICAgICAgICAgPC94bXBNTTpIaXN0b3J5PgogICAgICAgICA8eG1wTU06RGVyaXZlZEZyb20gcmRmOnBhcnNlVHlwZT0iUmVzb3VyY2UiPgogICAgICAgICAgICA8c3RSZWY6aW5zdGFuY2VJRD54bXAuaWlkOmQ0ZjMzNDFjLTRkYjctZjc0YS1iZTAxLWYxMGEwMzNhNjg4ZDwvc3RSZWY6aW5zdGFuY2VJRD4KICAgICAgICAgICAgPHN0UmVmOmRvY3VtZW50SUQ+MEIzOTNDRjk1RDQ0RDlGMDNFQjEzQkZEQ0UxRDA5MjM8L3N0UmVmOmRvY3VtZW50SUQ+CiAgICAgICAgICAgIDxzdFJlZjpvcmlnaW5hbERvY3VtZW50SUQ+MEIzOTNDRjk1RDQ0RDlGMDNFQjEzQkZEQ0UxRDA5MjM8L3N0UmVmOm9yaWdpbmFsRG9jdW1lbnRJRD4KICAgICAgICAgPC94bXBNTTpEZXJpdmVkRnJvbT4KICAgICAgICAgPGRjOmZvcm1hdD5pbWFnZS9wbmc8L2RjOmZvcm1hdD4KICAgICAgICAgPHBob3Rvc2hvcDpDb2xvck1vZGU+MzwvcGhvdG9zaG9wOkNvbG9yTW9kZT4KICAgICAgICAgPHBob3Rvc2hvcDpJQ0NQcm9maWxlPnNSR0IgSUVDNjE5NjYtMi4xPC9waG90b3Nob3A6SUNDUHJvZmlsZT4KICAgICAgICAgPHhtcDpDcmVhdGVEYXRlPjIwMTgtMDQtMDJUMTY6MjM6NTUrMDg6MDA8L3htcDpDcmVhdGVEYXRlPgogICAgICAgICA8eG1wOk1vZGlmeURhdGU+MjAxOC0wNC0wMlQxNjo0MToxMCswODowMDwveG1wOk1vZGlmeURhdGU+CiAgICAgICAgIDx4bXA6TWV0YWRhdGFEYXRlPjIwMTgtMDQtMDJUMTY6NDE6MTArMDg6MDA8L3htcDpNZXRhZGF0YURhdGU+CiAgICAgICAgIDx4bXA6Q3JlYXRvclRvb2w+QWRvYmUgUGhvdG9zaG9wIEVsZW1lbnRzIDE0LjAgKFdpbmRvd3MpPC94bXA6Q3JlYXRvclRvb2w+CiAgICAgICAgIDx0aWZmOkltYWdlV2lkdGg+MjU0PC90aWZmOkltYWdlV2lkdGg+CiAgICAgICAgIDx0aWZmOkltYWdlTGVuZ3RoPjI1NDwvdGlmZjpJbWFnZUxlbmd0aD4KICAgICAgICAgPHRpZmY6Qml0c1BlclNhbXBsZT4KICAgICAgICAgICAgPHJkZjpTZXE+CiAgICAgICAgICAgICAgIDxyZGY6bGk+ODwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPjg8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT44PC9yZGY6bGk+CiAgICAgICAgICAgIDwvcmRmOlNlcT4KICAgICAgICAgPC90aWZmOkJpdHNQZXJTYW1wbGU+CiAgICAgICAgIDx0aWZmOlBob3RvbWV0cmljSW50ZXJwcmV0YXRpb24+MjwvdGlmZjpQaG90b21ldHJpY0ludGVycHJldGF0aW9uPgogICAgICAgICA8dGlmZjpPcmllbnRhdGlvbj4xPC90aWZmOk9yaWVudGF0aW9uPgogICAgICAgICA8dGlmZjpTYW1wbGVzUGVyUGl4ZWw+MzwvdGlmZjpTYW1wbGVzUGVyUGl4ZWw+CiAgICAgICAgIDx0aWZmOlhSZXNvbHV0aW9uPjcyMDAwMC8xMDAwMDwvdGlmZjpYUmVzb2x1dGlvbj4KICAgICAgICAgPHRpZmY6WVJlc29sdXRpb24+NzIwMDAwLzEwMDAwPC90aWZmOllSZXNvbHV0aW9uPgogICAgICAgICA8dGlmZjpSZXNvbHV0aW9uVW5pdD4yPC90aWZmOlJlc29sdXRpb25Vbml0PgogICAgICAgICA8ZXhpZjpFeGlmVmVyc2lvbj4wMjIxPC9leGlmOkV4aWZWZXJzaW9uPgogICAgICAgICA8ZXhpZjpDb2xvclNwYWNlPjE8L2V4aWY6Q29sb3JTcGFjZT4KICAgICAgICAgPGV4aWY6UGl4ZWxYRGltZW5zaW9uPjE1MDwvZXhpZjpQaXhlbFhEaW1lbnNpb24+CiAgICAgICAgIDxleGlmOlBpeGVsWURpbWVuc2lvbj4xNTA8L2V4aWY6UGl4ZWxZRGltZW5zaW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAg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);
        background-size: 22px 22px;
        -moz-background-size: 22px 22px;
        background-repeat: no-repeat;
        position: absolute;
        top: 5px;
        right: 5px;
        height: 22px;
        z-index: 99;
        width: 22px;
    }
    .popup_window {
        display: none;
        position: relative;
        left: 0px;
        top: 0px;
        /*border: solid #627173 1px; */
        padding: 10px;
        /*background-color: #E6E6D6; */
        font-family: "Lucida Console", "Courier New", Courier, monospace;
        text-align: left;
        font-size: 8pt;
        /* width: 500px;*/
    }

    }
    /* -- report ------------------------------------------------------------------------ */
    #show_detail_line {
        margin-top: 3ex;
        margin-bottom: 1ex;
    }
    #result_table {
        width: 99%;
    }
    #header_row {
        font-weight: bold;
        color: #303641;
        background-color: #ebebeb;
    }
    #total_row  { font-weight: bold; }
    .passClass  { background-color: #bdedbc; }
    .failClass  { background-color: #ffefa4; }
    .errorClass { background-color: #ffc9c9; }
    .passCase   { color: #6c6; }
    .failCase   { color: #FF6600; font-weight: bold; }
    .errorCase  { color: #c00; font-weight: bold; }
    .hiddenRow  { display: none; }
    .testcase   { margin-left: 2em; }


    /* -- ending ---------------------------------------------------------------------- */
    #ending {
    }

    #div_base {
                position:absolute;
                top:0%;
                left:5%;
                right:5%;
                width: auto;
                height: auto;
                margin: -15px 0 0 0;
    }
</style>
"""

    # ------------------------------------------------------------------------
    # Heading
    #

    HEADING_TMPL = """
    <div class='page-header'>
        <h1 id="title">%(title)s</h1>
    %(parameters)s
    </div>
    <!--<div style="float: left;width:50%%;"><p class='description'>%(description)s</p></div>-->
    <div id="chartline" style="width:50%%;height:400px;float:left;"></div>
    <div id="chart" style="width:50%%;height:400px;float:left;"></div>
    <select name = "testTime" id = "testTime" style="height: 30px;height: 30px; width:250px;margin: 5px;margin-left: 0px" onchange="changeResult(this)">
        <!--<option value = "">请选择</option>-->
    </select>
    <p style="color:#999">*注<strong>: </strong>只保留最近十次的测试记录</p>
"""  # variables: (title, parameters, description)

    HEADING_ATTRIBUTE_TMPL = """<p class='attribute'><strong>%(name)s:</strong> %(value)s</p>
"""  # variables: (name, value)

    # ------------------------------------------------------------------------
    # Report
    #

    REPORT_TMPL = u"""
    <div id="btn-group">
    <div class="btn-group btn-group-sm">
        <a class="btn btn-primary" onclick='javascript:showCase(0)'>概要{ %(passrate)s }</a>
        <a class="btn btn-warning" onclick='javascript:showCase(4)'>错误{ %(error)s }</a>
        <a class="btn btn-danger" onclick='javascript:showCase(1)'>失败{ %(fail)s }</a>
        <a class="btn btn-success" onclick='javascript:showCase(2)'>通过{ %(Pass)s }</a>
        <a class="btn btn-info" onclick='javascript:showCase(3)'>所有{ %(count)s }</a>
    </div>
    <p></p>
    <table id='result_table' class="table table-bordered">
        <colgroup>
            <col align='left' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
        </colgroup>
        <tr id='header_row'>
            <td>测试套件/测试用例</td>
            <td>总数</td>
            <td>通过</td>
            <td>失败</td>
            <td>错误</td>
            <th>视图</th>
            <th>错误截图</th>
        </tr>
        %(test_list)s
        <tr id='total_row'>
            <td>总计</td>
            <td>%(count)s</td>
            <td>%(Pass)s</td>
            <td>%(fail)s</td>
            <td>%(error)s</td>
            <td>&nbsp;</td>
            <th>&nbsp;</th>
        </tr>
    </table>
    </div>
"""  # variables: (test_list, count, Pass, fail, error)

    REPORT_CLASS_TMPL = u"""
    <tr class='%(style)s'>
        <td>%(desc)s</td>
        <td>%(count)s</td>
        <td>%(Pass)s</td>
        <td>%(fail)s</td>
        <td>%(error)s</td>
        <td><a href="javascript:showClassDetail('%(cid)s',%(count)s)">详情</a></td>
        <td>&nbsp;</td>
    </tr>
"""  # variables: (style, desc, count, Pass, fail, error, cid)

    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center'>

    <!--css div popup start-->
    <a class="popup_link" onfocus='this.blur();' href="javascript:showTestDetail('div_%(tid)s')" >
        %(status)s</a>

    <div id='div_%(tid)s' class="popup_window">
        <div style='text-align: right; color:red;cursor:pointer'>
            <a onfocus='this.blur();' onclick="document.getElementById('div_%(tid)s').style.display = 'none' " >
               [x]</a>
        </div>
        <pre>%(script)s</pre>
    </div>
    <!--css div popup end-->

    </td>
    <td>%(img)s</td>
</tr>
"""  # variables: (tid, Class, style, desc, status)

    REPORT_TEST_NO_OUTPUT_TMPL = r"""
<tr id='%(tid)s' class='%(Class)s'>
    <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
    <td colspan='5' align='center'>%(status)s</td>
    <td>%(img)s</td>
</tr>
"""  # variables: (tid, Class, style, desc, status)

    REPORT_TEST_OUTPUT_TMPL = r"""%(id)s: %(output)s"""  # variables: (id, output)

    IMG_TMPL = r"""
        <a href="#"  onclick="show_img(this)">显示截图</a>
    <div align="center" class="screenshots"  style="display:none;z-index:2000">
        <a class="close_shots"  href="#"   onclick="hide_img(this)"></a>
        %(imgs)s
        <div class="imgyuan"></div>
    </div>
    """

    # ------------------------------------------------------------------------
    # ENDING
    #

    ENDING_TMPL = """<div id='ending'>&nbsp;</div>"""

    # -------------------- The end of the Template class -------------------
    def __getattribute__(self, item):
        value = object.__getattribute__(self, item)
        if PY3K:
            return value
        else:
            if isinstance(value, str):
                return value.decode("utf-8")
            else:
                return value


TestResult = unittest.TestResult


class _TestResult(TestResult):
    # note: _TestResult is a pure representation of results.
    # It lacks the output and reporting ability compares to unittest._TextTestResult.

    def __init__(self, verbosity=1, retry=0, save_last_try=True):
        TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.verbosity = verbosity

        # result is a list of result in 4 tuple
        # (
        #   result code (0: success; 1: fail; 2: error),
        #   TestCase object,
        #   Test output (byte string),
        #   stack trace,
        # )
        self.result = []
        self.retry = retry
        self.trys = 0
        self.status = 0
        self.save_last_try = save_last_try
        self.outputBuffer = StringIO.StringIO()

    def startTest(self, test):
        test.imgs = []
        TestResult.startTest(self, test)
        # just one buffer for both stdout and stderr
        self.outputBuffer.seek(0)
        self.outputBuffer.truncate()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        """
        Disconnect output redirection and return buffer.
        Safe to call multiple times.
        """
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()

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

    def addSuccess(self, test):
        self.success_count += 1
        self.status = 0
        TestResult.addSuccess(self, test)
        output = self.complete_output()
        self.result.append((0, test, output, ''))
        if self.verbosity > 1:
            sys.stderr.write('ok ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('.')

    def addError(self, test, err):
        self.error_count += 1
        self.status = 1
        TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str))
        if not getattr(test, "driver",""):
            pass
        else:
            try:
                driver = getattr(test, "driver")
                test.imgs.append(driver.get_screenshot_as_base64())
            except Exception:
                pass
        if self.verbosity > 1:
            sys.stderr.write('E  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('E')

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


class HTMLTestRunner(Template_mixin):

    def __init__(self, stream=sys.stdout, verbosity=1, title=None, description=None, retry=0, save_last_try=False):
        self.stream = stream
        self.retry = retry
        self.save_last_try = save_last_try
        self.verbosity = verbosity
        self.path = ""
        if title is None:
            self.title = self.DEFAULT_TITLE
        else:
            self.title = title
        if description is None:
            self.description = self.DEFAULT_DESCRIPTION
        else:
            self.description = description

        self.startTime = datetime.datetime.now()

    def run(self, test):
        """Run the given test case or test suite."""
        result = _TestResult(self.verbosity)
        test(result)
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        if PY3K:
            # for python3
            # print('\nTime Elapsed: %s' % (self.stopTime - self.startTime),file=sys.stderr)
            output = '\nTime Elapsed: %s' % (self.stopTime - self.startTime)
            sys.stderr.write(output)
        else:
            print >> sys.stderr, '\nTime Elapsed: %s' % (self.stopTime - self.startTime)
        return result

    def sortResult(self, result_list):
        # unittest does not seems to run in any particular order.
        # Here at least we want to group them together by class.
        rmap = {}
        classes = []
        for n,t,o,e in result_list:
            cls = t.__class__
            if cls not in rmap:
                rmap[cls] = []
                classes.append(cls)
            rmap[cls].append((n,t,o,e))
        r = [(cls, rmap[cls]) for cls in classes]
        return r

    def getReportAttributes(self, result):
        """
        Return report attributes as a list of (name, value).
        Override this to add custom attributes.
        """
        startTime = str(self.startTime)[:19]
        duration = str(self.stopTime - self.startTime)
        status = []
        if result.success_count: status.append(u'通过 %s' % result.success_count)
        if result.failure_count: status.append(u'失败 %s' % result.failure_count)
        if result.error_count:   status.append(u'错误 %s' % result.error_count  )
        if status:
            status = ' '.join(status)
        else:
            status = 'none'
        return [
            (u'开始时间', startTime),
            (u'运行时长', duration),
            (u'状态', status),
        ]

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

    def generateReport(self, test, result):
        report_attrs = self.getReportAttributes(result)
        generator = 'HTMLTestRunner %s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        self.path = os.path.splitext(self.stream.name)[0] + ".json"
        if self.mkdir_json():
            self.Write(saxutils.escape(self.title), report_attrs, saxutils.escape(self.description), report)
        ending = self._generate_ending()
        chart = self._generate_chart(result)
        output = self.HTML_TMPL % dict(
            jsonpath = os.path.split(self.path)[1],
            title = saxutils.escape(self.title),
            generator = generator,
            stylesheet = stylesheet,
            heading = heading,
            report = report,
            ending = ending,
            chart_script = chart
        )
        if PY3K:
            self.stream.write(output.encode())
        else:
            self.stream.write(output.encode('utf8'))

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                name = saxutils.escape(name),
                value = saxutils.escape(value),
            )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title = saxutils.escape(self.title),
            parameters = ''.join(a_lines),
            description = saxutils.escape(self.description)
        )
        return heading

    def _generate_report(self, result):
        rows = []
        sortedResult = self.sortResult(result.result)
        for cid, (cls, cls_results) in enumerate(sortedResult):
            # subtotal for a class
            np = nf = ne = 0
            for n,t,o,e in cls_results:
                if n == 0: np += 1
                elif n == 1: nf += 1
                else: ne += 1

            # format class description
            if cls.__module__ == "__main__":
                name = cls.__name__
            else:
                name = "%s.%s" % (cls.__module__, cls.__name__)
            doc = cls.__doc__ and cls.__doc__.split("\n")[0] or ""
            desc = doc and '%s: %s' % (name, doc) or name

            row = self.REPORT_CLASS_TMPL % dict(
                style = ne > 0 and 'errorClass' or nf > 0 and 'failClass' or 'passClass',
                desc = desc,
                count = np+nf+ne,
                Pass = np,
                fail = nf,
                error = ne,
                cid = 'c%s' % (cid+1),
            )
            rows.append(row)

            for tid, (n,t,o,e) in enumerate(cls_results):
                self._generate_report_test(rows, cid, tid, n, t, o, e)

        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
            count = str(result.success_count+result.failure_count+result.error_count),
            Pass = str(result.success_count),
            fail = str(result.failure_count),
            error = str(result.error_count),
            passrate = str("%.2f%%" % (float(result.success_count) /
                                     float(result.success_count + result.failure_count + result.error_count) * 100)
                         ),
        )
        return report

    def _generate_chart(self, result):
        chart = self.ECHARTS_SCRIPT % dict(
            Pass=str(result.success_count),
            fail=str(result.failure_count),
            error=str(result.error_count),
        )
        return chart

    def _generate_report_test(self, rows, cid, tid, n, t, o, e):
        # e.g. 'pt1.1', 'ft1.1', etc
        has_output = bool(o or e)
        tid = (n == 0 and 'p' or 'f') + 't%s.%s' % (cid + 1, tid + 1)
        name = t.id().split('.')[-1]
        if self.verbosity > 1:
            doc = t._testMethodDoc or ''
        else:
            doc = ""

        desc = doc and ('%s: %s' % (name, doc)) or name
        if not PY3K:
            if isinstance(desc, str):
                desc = desc.decode("utf-8")
        tmpl = has_output and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL

        # o and e should be byte string because they are collected from stdout and stderr?
        if isinstance(o, str):
            # uo = unicode(o.encode('string_escape'))
            if PY3K:
                uo = o
            else:
                uo = o.decode('utf-8', 'ignore')
        else:
            uo = o
        if isinstance(e, str):
            # ue = unicode(e.encode('string_escape'))
            if PY3K:
                ue = e
            elif e.find("Error") != -1 or e.find("Exception") != -1:
                es = e.decode('utf-8', 'ignore').split('\n')
                es[-2] = es[-2].decode('unicode_escape')
                ue = u"\n".join(es)
            else:
                ue = e.decode('utf-8', 'ignore')
        else:
            ue = e

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id=tid,
            output=saxutils.escape(uo + ue),
        )
        if getattr(t,'imgs',[]):
            # 判断截图列表，如果有则追加
            tmp = u""
            for i, img in enumerate(t.imgs):
                if i==0:
                    tmp+=""" <img src="data:image/jpg;base64,%s" style="display: block;" class="img"/>\n""" % img
                else:
                    tmp+=""" <img src="data:image/jpg;base64,%s" style="display: none;" class="img"/>\n""" % img
            imgs = self.IMG_TMPL % dict(imgs=tmp)
        else:
            imgs = u"""无截图"""

        row = tmpl % dict(
            tid=tid,
            Class=(n == 0 and 'hiddenRow' or 'none'),
            style=n == 2 and 'errorCase' or (n == 1 and 'failCase' or 'passCase'),
            desc=desc,
            script=script,
            status=self.STATUS[n],
            img=imgs,
        )
        rows.append(row)
        if not has_output:
            return

    def _generate_ending(self):
        return self.ENDING_TMPL


##############################################################################
# Facilities for running tests from the command line
##############################################################################

# Note: Reuse unittest.TestProgram to launch test. In the future we may
# build our own launcher to support more specific command line
# parameters like test title, CSS, etc.
class TestProgram(unittest.TestProgram):
    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """
    def runTests(self):
        # Pick HTMLTestRunner as the default test runner.
        # base class's testRunner parameter is not useful because it means
        # we have to instantiate HTMLTestRunner before we know self.verbosity.
        if self.testRunner is None:
            self.testRunner = HTMLTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)

main = TestProgram

##############################################################################
# Executing this module from the command line
##############################################################################

if __name__ == "__main__":
    main(module=None)
