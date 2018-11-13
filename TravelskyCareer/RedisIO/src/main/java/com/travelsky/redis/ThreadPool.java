package com.travelsky.redis;

import java.util.ArrayList;
import java.util.List;

/**
 * key:ip|Threadpool
 * value:时间|主机名|总量|使用|剩余|使用率|剩余率
 * 10.5.73.45|Threadpool|AutoBOXServer|8109   20180517-01:06:14|VM-VMW85689-JBS|-1|-1|0|100.000000|0.000000
 * 10.5.73.45|Threadpool|AutoBOXServer|8109   20180517-01:06:47|VM-VMW85689-JBS|-1|-1|0|100.000000|0.000000
 * 10.5.73.45|Threadpool|AutoBOXServer|8109   20180517-01:10:03||-1|-1|0|100.000000|0.000000
 * 10.5.73.45|Threadpool|AutoBOXServer|8109   20180517-01:10:12||-1|-1|0|100.000000|0.000000
 */

public class ThreadPool implements Metric{
    private String ip;
    private String metric;
    private List<ThreadPoolValue> threadPoolValues = new ArrayList<>();


    @Override
    public void addValue(MetricValue metricValue) {
        threadPoolValues.add((ThreadPoolValue) metricValue);
    }

    public List<ThreadPoolValue> getThreadPoolValues() {
        return threadPoolValues;
    }


    public String getIp() {
        return ip;
    }

    @Override
    public void setIp(String ip) {
        this.ip = ip;
    }

    public String getMetric() {
        return metric;
    }

    @Override
    public void setMetric(String metric) {
        this.metric = metric;
    }
}

class ThreadPoolValue implements MetricValue{
    private String time;
    private String hostname;
    private long totalNum;
    private long usage;
    private long free;
    private double usageRatio;
    private double surplusRatio;

    public String getTime() {
        return time;
    }

    @Override
    public void setTime(String time) {
        this.time = time;
    }

    public String getHostname() {
        return hostname;
    }

    @Override
    public void setHostname(String hostname) {
        this.hostname = hostname;
    }

    public long getTotalNum() {
        return totalNum;
    }

    public void setTotalNum(long totalNum) {
        this.totalNum = totalNum;
    }

    public long getUsage() {
        return usage;
    }

    public void setUsage(long usage) {
        this.usage = usage;
    }

    public long getFree() {
        return free;
    }

    public void setFree(long free) {
        this.free = free;
    }

    public double getUsageRatio() {
        return usageRatio;
    }

    public void setUsageRatio(double usageRatio) {
        this.usageRatio = usageRatio;
    }

    public double getSurplusRatio() {
        return surplusRatio;
    }

    public void setSurplusRatio(double surplusRatio) {
        this.surplusRatio = surplusRatio;
    }
}
